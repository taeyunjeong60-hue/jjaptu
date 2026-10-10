#--------모듈 불러오기--------
import asyncio
import json
import secrets
import websockets

#--------서버 연결 설정--------
HOST = ""
PORT = 65535

#--------접속자 및 방 정보 저장 공간--------
connected_clients = set()
name_dic = {}
rooms = {}  # room_id: {"owner": websocket, "members": [websocket]}

#--------닉네임 조회 함수--------
def nickname_of(client):
    return name_dic.get(client, "알 수 없음")

#--------방 정보 구성 함수--------
def room_payload(room_id, kind="room_update"):
    room = rooms[room_id]
    return {
        "type": kind,
        "room_id": room_id,
        "owner": nickname_of(room["owner"]),
        "members": [nickname_of(member) for member in room["members"]],
        "rounds": room.get("rounds", 10),
    }

#--------JSON 메시지 전송 함수--------
async def send_json(client, payload):
    await client.send(json.dumps(payload, ensure_ascii=False))

#--------전체 방 목록 전송 함수--------
async def send_room_list(client):
    items = []
    for room_id, room in rooms.items():
        items.append({
            "room_id": room_id,
            "owner": nickname_of(room["owner"]),
            "members_count": len(room["members"]),
            "rounds": room.get("rounds", 10),
        })
    await send_json(client, {"type": "room_list", "rooms": items})

async def broadcast_room_list():
    clients = list(connected_clients)
    if clients:
        results = await asyncio.gather(*(send_room_list(c) for c in clients), return_exceptions=True)
        for client, result in zip(clients, results):
            if isinstance(result, Exception):
                print(f"방 목록 전송 실패: {result}")

#--------방 참가자에게 최신 방 정보 전송--------
async def broadcast_room(room_id):
    room = rooms.get(room_id)
    if not room:
        return
    clients = list(room["members"])
    payload = json.dumps(room_payload(room_id), ensure_ascii=False)
    results = await asyncio.gather(*(client.send(payload) for client in clients), return_exceptions=True)
    for client, result in zip(clients, results):
        if isinstance(result, Exception):
            print(f"방 정보 전송 실패({room_id}): {result}")

#--------방에서 나가기 처리--------
async def leave_room(client, notify=True):
    for room_id in list(rooms):
        room = rooms[room_id]
        if client not in room["members"]:
            continue
        room["members"].remove(client)
        if not room["members"]:
            del rooms[room_id]
            print(f"빈 방 삭제: {room_id}")
        else:
            if room["owner"] is client:
                room["owner"] = room["members"][0]
            await broadcast_room(room_id)
        if notify and client in connected_clients:
            await send_json(client, {"type": "room_left"})
        await broadcast_room_list()
        return

#--------클라이언트 요청 처리 함수--------
async def handler(websocket):
    connected_clients.add(websocket)
    print(f"접속: {websocket.remote_address} / 접속자 {len(connected_clients)}명")
    await send_room_list(websocket)
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                message = message.decode("utf-8", errors="replace")
            print(f"클라이언트 메시지: {message}")

            #--------닉네임 등록--------
            if message.startswith("name,"):
                nickname = message.partition(",")[2].strip()[:10]
                if not nickname:
                    await send_json(websocket, {"type": "error", "message": "닉네임을 입력해주세요."})
                    continue
                name_dic[websocket] = nickname
                await send_json(websocket, {"type": "name_ok", "nickname": nickname})
                await send_room_list(websocket)

            #--------방 생성--------
            elif message == "makeroom" or message.startswith("makeroom,"):
                if not name_dic.get(websocket):
                    await send_json(websocket, {"type": "error", "message": "먼저 닉네임을 등록해주세요."})
                    continue

                #--------방 생성 설정 검증--------
                try:
                    rounds = int(message.partition(",")[2]) if "," in message else 10
                except ValueError:
                    rounds = 0
                allowed_rounds = {5, 10, 20}
                if rounds not in allowed_rounds:
                    await send_json(websocket, {
                        "type": "error",
                        "message": "라운드 수는 5, 10, 20 중에서 선택해주세요."
                    })
                    continue

                await leave_room(websocket, notify=False)
                room_id = secrets.token_hex(3).upper()
                while room_id in rooms:
                    room_id = secrets.token_hex(3).upper()
                rooms[room_id] = {
                    "owner": websocket,
                    "members": [websocket],
                    "rounds": rounds,
                }
                await send_json(websocket, room_payload(room_id, "makeroom_ok"))
                await broadcast_room_list()
                print(f"방 생성: ID={room_id}, 방장={nickname_of(websocket)}, 라운드={rounds}")

            #--------방 목록 요청--------
            elif message == "listrooms":
                await send_room_list(websocket)

            #--------특정 방 입장--------
            elif message.startswith("joinroom,") or message == "enterroom":
                if not name_dic.get(websocket):
                    await send_json(websocket, {"type": "error", "message": "먼저 닉네임을 등록해주세요."})
                    continue
                if message.startswith("joinroom,"):
                    room_id = message.partition(",")[2].strip().upper()
                else:
                    room_id = next(iter(rooms), "")
                if not room_id or room_id not in rooms:
                    await send_json(websocket, {"type": "error", "message": "입장 가능한 방이 없습니다."})
                    continue
                await leave_room(websocket, notify=False)
                room = rooms.get(room_id)
                if room is None:
                    await send_json(websocket, {"type": "error", "message": "해당 방이 이미 사라졌습니다."})
                    continue
                if websocket not in room["members"]:
                    room["members"].append(websocket)
                await send_json(websocket, room_payload(room_id, "room_joined"))
                await broadcast_room(room_id)
                await broadcast_room_list()

            #--------방 나가기--------
            elif message == "leaveroom":
                await leave_room(websocket)

            else:
                await send_json(websocket, {"type": "error", "message": "알 수 없는 요청입니다."})

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await leave_room(websocket, notify=False)
        connected_clients.discard(websocket)
        name_dic.pop(websocket, None)
        await broadcast_room_list()
        print(f"연결 종료: {websocket.remote_address} / 접속자 {len(connected_clients)}명")

#--------WebSocket 서버 실행 함수--------
async def main():
    async with websockets.serve(handler, HOST, PORT, ping_interval=20, ping_timeout=20, max_size=1_000_000):
        print(f"WebSocket 서버 시작: {HOST or '0.0.0.0'}:{PORT}")
        await asyncio.Future()

#--------프로그램 시작--------
if __name__ == "__main__":
    asyncio.run(main())
