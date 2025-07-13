from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import socketio
from fastapi.middleware.cors import CORSMiddleware

sio = socketio.AsyncServer(async_mode='asgi')
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app_mount = socketio.ASGIApp(sio, app)

rooms = {}

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@sio.event
async def connect(sid, environ):
    print("🔌 클라이언트 연결됨:", sid)

@sio.event
async def join(sid, data):
    room = data["room"]
    name = data["name"]

    if room not in rooms:
        rooms[room] = {"players": {}, "turn": None, "wins": {}}

    if len(rooms[room]["players"]) >= 2:
        await sio.emit("error", {"msg": "방이 꽉 찼습니다."}, to=sid)
        return

    await sio.enter_room(sid, room)

    rooms[room]["players"][sid] = {
        "name": name,
        "secret": None,
        "ready": False,
    }
    rooms[room]["wins"][sid] = rooms[room]["wins"].get(sid, 0)

    if len(rooms[room]["players"]) == 2:
        await sio.emit("start", {"msg": "게임 시작!"}, room=room)

@sio.event
async def set_secret(sid, data):
    room = data["room"]
    secret = data["secret"]
    rooms[room]["players"][sid]["secret"] = secret
    rooms[room]["players"][sid]["ready"] = True
    if all(p["ready"] for p in rooms[room]["players"].values()):
        players = list(rooms[room]["players"].keys())
        rooms[room]["turn"] = players[0]
        await sio.emit("turn", {"your_turn": rooms[room]["turn"]}, room=room)

@sio.event
async def guess(sid, data):
    room = data["room"]
    guess = data["guess"]
    players = rooms[room]["players"]
    opponent_sid = [k for k in players if k != sid][0]
    secret = players[opponent_sid]["secret"]
    strikes = sum(a == b for a, b in zip(secret, guess))
    balls = len(set(secret) & set(guess)) - strikes
    result = "아웃" if strikes == 0 and balls == 0 else f"{strikes}S {balls}B"
    win = strikes == len(secret)

    await sio.emit("guess_result", {
        "from": players[sid]["name"],
        "guess": guess,
        "result": result,
        "win": win
    }, room=room)

    if win:
        rooms[room]["wins"][sid] += 1
        await sio.emit("game_over", {
            "winner": players[sid]["name"],
            "wins": rooms[room]["wins"]
        }, room=room)
    else:
        rooms[room]["turn"] = opponent_sid
        await sio.emit("turn", {"your_turn": opponent_sid}, room=room)

@sio.event
async def restart(sid, data):
    room = data["room"]
    for player in rooms[room]["players"].values():
        player["secret"] = None
        player["ready"] = False
    await sio.emit("start", {"msg": "게임 다시 시작!"}, room=room)