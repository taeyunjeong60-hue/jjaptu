import asyncio
import websockets

HOST = ""  # 모든 네트워크 인터페이스에서 수신
PORT = 65535

connected_clients = set()
name_dic = {}
rooms = []

# -------------------------------------------------
# 함수
# -------------------------------------------------

# broadcast - 확성기
async def broadcast(message, exclude=None):
    """연결된 WebSocket에 메시지를 전송하고 끊어진 연결은 정리."""
    targets = [
        client for client in connected_clients
        if client is not exclude
    ]
    if not targets:
        return

    results = await asyncio.gather(
        *(client.send(message) for client in targets),
        return_exceptions=True,
    )
    for client, result in zip(targets, results):
        if isinstance(result, Exception):
            print(f"브로드캐스트 실패: {result}")
            connected_clients.discard(client)
            name_dic.pop(client, None)

# -------------------------------------------------
# 해더 (메세지 수신, 전송)
# -------------------------------------------------

async def handler(websocket):
    connected_clients.add(websocket)
    print(
        f"클라이언트 접속: {websocket.remote_address}"
        f"현재 접속자 수: {len(connected_clients)}"
    )

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                message = message.decode("utf-8", errors="replace")

            print(f"클라이언트 메시지: {message}")

            if message.startswith("name,"):
                nickname = message.partition(",")[2].strip()
                if not nickname:
                    await websocket.send("error,닉네임이 비어 있습니다.")
                    continue
                name_dic[websocket] = nickname
                await websocket.send("name_ok")
                print(f"닉네임 등록: {nickname}")

            elif message == "makeroom":
                nickname = name_dic.get(websocket)
                if not nickname:
                    await websocket.send("error,먼저 닉네임을 등록해주세요.")
                    continue

                rooms.append({"owner": websocket, "members": [websocket]})
                # 방을 만든 클라이언트에도 응답을 보내 recv 대기 때문에 멈추지 않게 함
                await websocket.send("makeroom_ok")
                await broadcast(f"room_created,{nickname}", exclude=websocket)
                print(f"방 생성: {nickname} / 총 방 수: {len(rooms)}")

            elif message == "enterroom":
                if not rooms:
                    await websocket.send("error,입장 가능한 방이 없습니다.")
                    continue

                room = rooms[0]
                if websocket not in room["members"]:
                    room["members"].append(websocket)
                await websocket.send("enterroom_ok")
                await broadcast(
                    f"player_joined,{name_dic.get(websocket, '알 수 없음')}",
                    exclude=websocket,
                )

            else:
                await websocket.send("error,알 수 없는 요청입니다.")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        name_dic.pop(websocket, None)
        for room in rooms[:]:
            if websocket in room["members"]:
                room["members"].remove(websocket)
            if not room["members"]:
                rooms.remove(room)
        print(
            f"클라이언트 연결 종료: {websocket.remote_address}"
            f"현재 접속자 수: {len(connected_clients)}"
        )

# -------------------------------------------------
# 서버 시작
# -------------------------------------------------

async def main():
    async with websockets.serve(
        handler,
        HOST,
        PORT,
        ping_interval=20,
        ping_timeout=20,
        max_size=1_000_000,
    ):
        print(f"서버 시작: {HOST or '0.0.0.0'}:{PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
