let socket = io();
let username = "";
let isDrawer = false;

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
let drawing = false;

function joinGame() {
    username = document.getElementById("username").value;
    socket.emit("join", { username });
}

socket.on("player_list", (data) => {
    const scoreboard = document.getElementById("scoreboard");
    scoreboard.innerHTML = "";
    data.players.forEach(player => {
        let score = data.scores[player];
        scoreboard.innerHTML += `<li>${player}: ${score}</li>`;
    });
});

socket.on("start_round", (data) => {
    isDrawer = data.drawer === username;
    document.getElementById("status").innerText = isDrawer
        ? `You're drawing: ${data.word}`
        : `Waiting for ${data.drawer} to draw...`;
    clearCanvas();
});

socket.on("draw", (data) => {
    draw(data.x, data.y);
});

canvas.addEventListener("mousedown", () => { if (isDrawer) drawing = true; });
canvas.addEventListener("mouseup", () => drawing = false);
canvas.addEventListener("mousemove", (e) => {
    if (drawing && isDrawer) {
        const x = e.offsetX;
        const y = e.offsetY;
        socket.emit("draw", { x, y });
        draw(x, y);
    }
});

function draw(x, y) {
    ctx.fillStyle = "black";
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, 2 * Math.PI);
    ctx.fill();
}

function clearCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function sendGuess() {
    const guess = document.getElementById("guessInput").value;
    socket.emit("guess", { username, guess });
    document.getElementById("guessInput").value = "";
}

socket.on("guess", (data) => {
    const chat = document.getElementById("chat");
    chat.innerHTML += `<p><b>${data.username}:</b> ${data.guess}</p>`;
});

socket.on("correct_guess", (data) => {
    const chat = document.getElementById("chat");
    chat.innerHTML += `<p><b>${data.username} guessed it! Word was "${data.word}"</b></p>`;
});

socket.on("round_end", (data) => {
    document.getElementById("status").innerText = data.message;
});

socket.on("timer", (data) => {
    document.getElementById("timer").innerText = data.time;
});
