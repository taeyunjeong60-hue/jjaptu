#--------모듈 불러오기--------
import asyncio
import json
import os
import pygame
import websockets

#--------서버 연결 설정--------
HOST = "192.168.0.54"  # 서버 컴퓨터의 IP 주소로 변경
PORT = 65535
SCREEN_WIDTH = 1408
SCREEN_HEIGHT = 768
FPS = 60

#--------화면 크기 및 색상 설정--------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGRAY = (30, 30, 30)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


#--------이미지 불러오기 함수--------
def load_image(path):
    image = pygame.image.load(path)
    return image.convert_alpha() if image.get_alpha() is not None else image.convert()


#--------서버 메시지 수신 함수--------
async def receive_messages(websocket, incoming):
    """서버 메시지를 별도 작업에서 수신해 Pygame 화면 루프가 멈추지 않게 한다."""
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                message = message.decode("utf-8", errors="replace")
            await incoming.put(message)
    except websockets.exceptions.ConnectionClosed:
        await incoming.put(json.dumps({"type": "connection_closed"}, ensure_ascii=False))


#--------화면 중앙에 글자 표시하는 함수--------
def draw_center_text(screen, font, text, center, color=WHITE):
    surface = font.render(str(text), True, color)
    screen.blit(surface, surface.get_rect(center=center))


#--------게임 메인 함수--------
async def main():
    #--------Pygame 초기화 및 화면 구성--------
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("끝말잇기 - 방 만들기 테스트")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("malgungothic", 44)
    font = pygame.font.SysFont("malgungothic", 32)
    small_font = pygame.font.SysFont("malgungothic", 22)

    enter_text = font.render("입장하기", True, DARKGRAY)
    enter_rect = enter_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 195))
    make_text = font.render("방 만들기", True, WHITE)
    make_rect = make_text.get_rect(center=(150, 100))
    join_text = font.render("방 입장", True, WHITE)
    join_rect = join_text.get_rect(center=(400, 100))
    name_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 80, 300, 50)
    enter_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 205, SCREEN_HEIGHT // 2 + 150, 410, 90)
    back_rect = pygame.Rect(30, SCREEN_HEIGHT - 80, 180, 48)

    #--------배경 이미지 불러오기--------
    image_dir = os.path.join(BASE_DIR, "image")
    try:
        background = load_image(os.path.join(image_dir, "background.png"))
        lobby_background = load_image(os.path.join(image_dir, "game_enter_background.png"))
    except (pygame.error, OSError) as exc:
        pygame.quit()
        raise SystemExit(f"배경 이미지를 불러오지 못했습니다. image 폴더를 확인하세요.\n{exc}")

    if background.get_size() != screen.get_size():
        background = pygame.transform.smoothscale(background, screen.get_size())
    if lobby_background.get_size() != screen.get_size():
        lobby_background = pygame.transform.smoothscale(lobby_background, screen.get_size())

    #--------WebSocket 서버 연결--------
    uri = f"ws://{HOST}:{PORT}"
    try:
        async with websockets.connect(
            uri, open_timeout=8, close_timeout=2,
            ping_interval=20, ping_timeout=20, max_size=1_000_000
        ) as websocket:
            incoming = asyncio.Queue()
            receiver = asyncio.create_task(receive_messages(websocket, incoming))

            #--------게임 상태 변수--------
            running = True
            page = "nickname"  # nickname -> lobby -> room
            input_active = False
            nickname = ""
            editing_text = ""
            status_message = "서버에 연결되었습니다."
            room_id = ""
            room_owner = ""
            room_members = []

            try:
                while running:
                    #--------서버에서 받은 메시지 처리--------
                    while not incoming.empty():
                        raw_message = incoming.get_nowait()
                        try:
                            data = json.loads(raw_message)
                        except (json.JSONDecodeError, TypeError):
                            # 기존 문자열 형식의 서버 응답도 상태 메시지로 표시
                            status_message = str(raw_message)
                            continue

                        kind = data.get("type", "")
                        if kind == "connection_closed":
                            status_message = "서버 연결이 끊어졌습니다."
                        elif kind == "name_ok":
                            status_message = "닉네임 등록 완료"
                        elif kind == "makeroom_ok":
                            room_id = data.get("room_id", "")
                            room_owner = data.get("owner", nickname)
                            room_members = data.get("members", [nickname])
                            page = "room"
                            status_message = "방이 생성되었습니다."
                        elif kind in ("room_update", "room_joined"):
                            room_id = data.get("room_id", room_id)
                            room_owner = data.get("owner", room_owner)
                            room_members = data.get("members", room_members)
                            if kind == "room_joined":
                                page = "room"
                            status_message = "방 정보가 업데이트되었습니다."
                        elif kind == "error":
                            status_message = data.get("message", "요청 처리 중 오류가 발생했습니다.")
                        elif kind == "room_created":
                            status_message = f"새 방이 생성되었습니다: {data.get('room_id', '')}"
                        elif kind == "room_left":
                            status_message = f"{data.get('nickname', '사용자')}가 방에서 나갔습니다."
                        else:
                            status_message = f"서버 메시지: {kind or raw_message}"
                        print(f"서버 메시지: {data}")

                    #--------마우스 및 키보드 입력 처리--------
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False

                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if page == "nickname" and name_rect.collidepoint(event.pos):
                                input_active = True
                                pygame.key.start_text_input()
                                pygame.key.set_text_input_rect(name_rect)
                            elif page == "nickname" and enter_button_rect.collidepoint(event.pos):
                                if nickname.strip():
                                    await websocket.send(f"name,{nickname.strip()}")
                                    input_active = False
                                    pygame.key.stop_text_input()
                                    page = "lobby"
                                else:
                                    status_message = "닉네임을 입력해주세요."
                            elif page == "lobby" and make_rect.collidepoint(event.pos):
                                await websocket.send("makeroom")
                                status_message = "방 생성 요청을 보냈습니다."
                            elif page == "lobby" and join_rect.collidepoint(event.pos):
                                await websocket.send("enterroom")
                                status_message = "방 입장 요청을 보냈습니다."
                            elif page == "room" and back_rect.collidepoint(event.pos):
                                await websocket.send("leaveroom")
                                status_message = "방 나가기 요청을 보냈습니다."
                        elif event.type == pygame.TEXTEDITING and input_active:
                            editing_text = event.text
                        elif event.type == pygame.TEXTINPUT and input_active:
                            if len(nickname) + len(event.text) <= 10:
                                nickname += event.text
                            editing_text = ""
                        elif event.type == pygame.KEYDOWN:
                            if input_active:
                                if event.key == pygame.K_BACKSPACE:
                                    if editing_text == "" and nickname:
                                        nickname = nickname[:-1]
                                elif event.key == pygame.K_RETURN:
                                    if nickname.strip():
                                        await websocket.send(f"name,{nickname.strip()}")
                                        input_active = False
                                        pygame.key.stop_text_input()
                                        page = "lobby"
                                    else:
                                        status_message = "닉네임을 입력해주세요."

                    #--------현재 화면 그리기--------
                    if page == "nickname":
                        screen.blit(background, (0, 0))
                        screen.blit(enter_text, enter_rect)
                        pygame.draw.rect(screen, WHITE, name_rect)
                        shown_name = nickname + editing_text
                        screen.blit(small_font.render(shown_name, True, BLACK), (name_rect.x + 10, name_rect.y + 10))
                    elif page == "lobby":
                        screen.blit(lobby_background, (0, 0))
                        screen.blit(make_text, make_rect)
                        screen.blit(join_text, join_rect)
                        draw_center_text(screen, small_font, "방 만들기를 눌러 새 방을 생성하세요.", (SCREEN_WIDTH // 2, 180))
                    else:
                        screen.blit(lobby_background, (0, 0))
                        draw_center_text(screen, title_font, "방 대기실", (SCREEN_WIDTH // 2, 100))
                        draw_center_text(screen, font, f"방 ID: {room_id}", (SCREEN_WIDTH // 2, 190))
                        draw_center_text(screen, font, f"방장: {room_owner}", (SCREEN_WIDTH // 2, 250))
                        draw_center_text(screen, font, f"참가자 ({len(room_members)})", (SCREEN_WIDTH // 2, 330))
                        for index, member in enumerate(room_members):
                            draw_center_text(screen, small_font, f"{index + 1}. {member}", (SCREEN_WIDTH // 2, 385 + index * 34))
                        pygame.draw.rect(screen, (50, 50, 50), back_rect, border_radius=8)
                        draw_center_text(screen, small_font, "뒤로", back_rect.center)

                    if status_message:
                        status_surface = small_font.render(status_message, True, WHITE)
                        screen.blit(status_surface, (15, SCREEN_HEIGHT - 30))
                    pygame.display.flip()
                    clock.tick(FPS)
                    await asyncio.sleep(0)
            finally:
                receiver.cancel()
                await asyncio.gather(receiver, return_exceptions=True)
    except (OSError, asyncio.TimeoutError, websockets.exceptions.WebSocketException) as exc:
        pygame.quit()
        raise SystemExit(f"서버에 연결할 수 없습니다: {uri}\nHOST, 포트, 서버 실행 상태를 확인하세요.\n{exc}")
    pygame.quit()


#--------프로그램 시작--------
if __name__ == "__main__":
    asyncio.run(main())
