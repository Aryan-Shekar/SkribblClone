# 👇 IMPORTANT: Patch eventlet BEFORE importing anything else
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random
import threading
import time

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

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    global round_active
    username = data['username']
    if username not in players:
        players.append(username)
        scores[username] = 0
    emit('player_list', {'players': players, 'scores': scores}, broadcast=True)
    if not round_active:
        start_round()

def start_round():
    global current_word, round_active
    round_active = True
    current_drawer = players[current_drawer_index]
    current_word = random.choice(words)

    socketio.emit('start_round', {
        'drawer': current_drawer,
        'word': current_word  # only drawer sees this
    })

    threading.Thread(target=round_timer).start()

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

def next_turn():
    global current_drawer_index, round_active
    current_drawer_index = (current_drawer_index + 1) % len(players)
    round_active = False
    time.sleep(3)
    start_round()

if __name__ == '__main__':
    import os
    PORT = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=PORT)


