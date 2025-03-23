# 👇 Patch eventlet BEFORE any other import
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random
import threading
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')

players = []
scores = {}
current_drawer_index = 0
current_word = ""
round_time = 60
round_active = False
words = ['apple', 'car', 'tree', 'house', 'sun', 'fish']

bot_name = "Bot_Player"
bot_active = False
bot_thread = None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    global round_active, bot_thread
    username = data['username']
    if username not in players:
        players.append(username)
        scores[username] = 0
    emit('player_list', {'players': players, 'scores': scores}, broadcast=True)

    if len(players) == 1 and not bot_thread:
        bot_thread = threading.Timer(30.0, activate_bot_if_alone)
        bot_thread.start()

    if not round_active and len(players) >= 1:
        start_round()

def activate_bot_if_alone():
    global bot_active
    if len(players) == 1 and not bot_active:
        players.append(bot_name)
        scores[bot_name] = 0
        bot_active = True
        socketio.emit('player_list', {'players': players, 'scores': scores}, broadcast=True)
        print("[BOT] Bot joined the game.")

def start_round():
    global current_word, round_active
    round_active = True
    current_drawer = players[current_drawer_index]
    current_word = random.choice(words)

    socketio.emit('start_round', {
        'drawer': current_drawer,
        'word': current_word if current_drawer != bot_name else None
    })

    threading.Thread(target=round_timer).start()

    if bot_active and current_drawer != bot_name:
        threading.Thread(target=bot_guess_loop).start()

def round_timer():
    global round_time, round_active
    time_left = round_time
    while time_left > 0 and round_active:
        socketio.emit('timer', {'time': time_left})
        time.sleep(1)
        time_left -= 1
    if round_active:
        socketio.emit('round_end', {'message': f"Time's up! The word was '{current_word}'"})
        next_turn()

@socketio.on('draw')
def handle_draw(data):
    emit('draw', data, broadcast=True)

@socketio.on('guess')
def handle_guess(data):
    global round_active
    username = data['username']
    guess = data['guess']
    if guess.strip().lower() == current_word.lower() and round_active:
        scores[username] += 10
        round_active = False
        socketio.emit('correct_guess', {'username': username, 'word': current_word})
        socketio.emit('player_list', {'players': players, 'scores': scores}, broadcast=True)
        next_turn()
    else:
        emit('guess', data, broadcast=True)

def bot_guess_loop():
    global round_active
    attempts = 0
    while round_active and attempts < 10:
        guess = random.choice(words)
        socketio.emit('guess', {'username': bot_name, 'guess': guess})
        if guess.lower() == current_word.lower():
            scores[bot_name] += 10
            round_active = False
            socketio.emit('correct_guess', {'username': bot_name, 'word': current_word})
            socketio.emit('player_list', {'players': players, 'scores': scores}, broadcast=True)
            next_turn()
            break
        time.sleep(3)
        attempts += 1

def next_turn():
    global current_drawer_index, round_active
    current_drawer_index = (current_drawer_index + 1) % len(players)
    round_active = False
    time.sleep(3)
    start_round()

if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=PORT)
