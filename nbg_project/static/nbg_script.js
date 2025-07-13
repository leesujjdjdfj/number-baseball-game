const socket = io();
let myRoom = null;

function joinGame() {
  const name = document.getElementById("name").value;
  const room = document.getElementById("room").value;
  myRoom = room;
  socket.emit("join", { name, room });
  document.getElementById("login").style.display = "none";
  document.getElementById("setup").style.display = "block";
}

function isValidSecret(secret, len) {
  return /^\d+$/.test(secret) && secret.length === len && new Set(secret).size === len;
}

function setSecret() {
  const secret = document.getElementById("secret").value;
  const len = parseInt(document.getElementById("length").value);
  if (!isValidSecret(secret, len)) {
    alert(`${len}자리의 중복 없는 숫자를 입력하세요.`);
    return;
  }
  socket.emit("set_secret", { secret, room: myRoom });
  document.getElementById("setup").style.display = "none";
  document.getElementById("game").style.display = "block";
}

function sendGuess() {
  const guess = document.getElementById("guess").value;
  socket.emit("guess", { guess, room: myRoom });
}

function requestRestart() {
  socket.emit("restart", { room: myRoom });
  document.getElementById("log").innerHTML = "";
  document.getElementById("status").textContent = "재시작 요청 중...";
}

socket.on("start", () => {
  document.getElementById("status").textContent = "상대방 입장 완료. 숫자를 설정하세요.";
  document.getElementById("guess").value = "";
});

socket.on("turn", (data) => {
  const isMyTurn = socket.id === data.your_turn;
  document.getElementById("status").textContent = isMyTurn
    ? "당신의 차례입니다!"
    : "상대의 차례입니다...";
});

socket.on("guess_result", (data) => {
  const log = document.getElementById("log");
  const item = document.createElement("li");
  item.textContent = `${data.from}: ${data.guess} → ${data.result}`;
  log.appendChild(item);
});

socket.on("game_over", (data) => {
  document.getElementById("status").textContent = `🎉 ${data.winner} 승리!`;
  document.getElementById("player1").textContent = `Player 1: ${Object.values(data.wins)[0]}승`;
  document.getElementById("player2").textContent = `Player 2: ${Object.values(data.wins)[1]}승`;
});

socket.on("error", (data) => {
  alert(data.msg);
});

function generateRoomCode() {
  const randomCode = "ROOM" + Math.floor(1000 + Math.random() * 9000);
  document.getElementById("room").value = randomCode;
}