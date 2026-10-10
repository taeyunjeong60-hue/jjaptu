#서버
import websockets
import asyncio

HOST=''
PORT=65535

connected_clients=set()
rooms=[]
name_dic={}

async def handler(websocket):
    connected_clients.add(websocket)
    print(f"클라이언트 접속: {websocket.remote_address} 현재 접속자 수: {len(connected_clients)}")

    try:
        async for message in websocket:
            print(f"클라이언트로부터 받은 메시지: {message}")
            if "name" in message:
                name=message.split(",")
                name_dic[websocket]=name[1]
                print(name_dic)
            elif message == "makeroom":
                rooms.append([websocket])
                await broadcast(websocket, message)
                print(rooms)
            elif message == "enterroom":
                if rooms:
                    rooms[0].append(websocket)
                    await websocket.send("enterroom")
    except websockets.exceptions.ConnectionClosed:
        print(f"클라이언트 연결 종료: {websocket.remote_address}")
    finally:
        connected_clients.discard(websocket)

async def broadcast(client_sockets, send_sock, msg):
    import re
    for broadcast in client_sockets:
        if broadcast != send_sock:
            try:
                values=re.findall(r"[\d.]+", str(broadcast))
                print((values[-2],int(values[-1])))
                await broadcast.sendto(f'{msg}{send_sock}'.encode('utf-8'),(values[-2],int(values[-1])))
            except Exception as e:
                print(f"전송 실패:{e}")

async def main():
    async with websockets.serve(handler, HOST, PORT):
        print(f"서버 시작: {HOST}:{PORT}")
        await asyncio.Future()  # 서버가 종료되지 않도록 대기

if __name__ == "__main__":
    asyncio.run(main())