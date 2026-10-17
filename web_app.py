"""Render용 단일 포트 웹 + WebSocket 서버."""
import asyncio
import os
from pathlib import Path

from aiohttp import WSMsgType, web
import jjaptu_server as game_server

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = (BASE_DIR / "build" / "web").resolve()


class WebSocketClientAdapter:
    """aiohttp WebSocket을 기존 게임 서버가 기대하는 인터페이스로 감쌉니다."""
    def __init__(self, ws, remote_address):
        self.ws = ws
        self.remote_address = remote_address

    async def send(self, message):
        await self.ws.send_str(message)

    def __aiter__(self):
        return self._messages()

    async def _messages(self):
        async for message in self.ws:
            if message.type == WSMsgType.TEXT:
                yield message.data
            elif message.type == WSMsgType.BINARY:
                yield message.data
            elif message.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR):
                break


async def index(request):
    return web.FileResponse(WEB_DIR / "index.html")


async def healthz(request):
    return web.json_response({"status": "ok"})


async def static_files(request):
    filename = request.match_info.get("filename", "")
    target = (WEB_DIR / filename).resolve()
    if not target.is_relative_to(WEB_DIR) or not target.is_file():
        raise web.HTTPNotFound()
    return web.FileResponse(target)


async def websocket_endpoint(request):
    ws = web.WebSocketResponse(heartbeat=20, max_msg_size=1_000_000)
    await ws.prepare(request)
    client = WebSocketClientAdapter(ws, request.remote)
    try:
        await game_server.handler(client)
    except (ConnectionError, RuntimeError) as exc:
        print(f"WebSocket 연결 종료: {exc}")
    finally:
        if not ws.closed:
            await ws.close()
    return ws


def create_app():
    app = web.Application(client_max_size=1_000_000)
    app.router.add_get("/healthz", healthz)
    app.router.add_get("/ws", websocket_endpoint)
    app.router.add_get("/", index)
    app.router.add_get("/{filename:.*}", static_files)
    return app


async def main():
    port = int(os.environ.get("PORT", "8000"))
    app = create_app()
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    print(f"짭투 베타 서버 시작: 0.0.0.0:{port}")
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
