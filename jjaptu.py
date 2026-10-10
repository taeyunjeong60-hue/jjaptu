import asyncio
import os
import pygame
import websockets

# -------------------------------------------------
# 기본 함수 정의 및 이미지 로딩
# -------------------------------------------------

# 서버 주소: 서버를 실행 중인 컴퓨터의 LAN IP로 설정
HOST = "172.30.1.73"
PORT = 65535

SCREEN_WIDTH = 1408
SCREEN_HEIGHT = 768
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGRAY = (30, 30, 30)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_image(path):
    """이미지를 시작할 때 한 번만 불러오고 빠른 blit 형식으로 변환."""
    image = pygame.image.load(path)
    return image.convert_alpha() if image.get_alpha() is not None else image.convert()


async def receive_messages(websocket, incoming):
    """서버 수신을 별도 작업으로 처리해 화면 루프가 recv() 때문에 멈추지 않게 함."""
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                message = message.decode("utf-8", errors="replace")
            await incoming.put(message)
    except websockets.exceptions.ConnectionClosed:
        await incoming.put("__CONNECTION_CLOSED__")

# -------------------------------------------------
# 메인 함수
# -------------------------------------------------

async def main():

    # -------------------------------------------------
    # 타이틀 설정 및 변수 정의(글자, 이미지, 범위)
    # -------------------------------------------------

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("끝말잇기")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("malgungothic", 40)
    small_font = pygame.font.SysFont("malgungothic", 20)

    enter_text = font.render("입장하기", True, DARKGRAY)
    enter_rect = enter_text.get_rect(
        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 195)
    )
    make_text = font.render("방 만들기", True, WHITE)
    make_rect = make_text.get_rect(center=(150, 100))
    join_text = font.render("방 입장", True, WHITE)
    join_rect = join_text.get_rect(center=(400, 100))

    name_rect = pygame.Rect(
        SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 80, 300, 50
    )
    enter_button_rect = pygame.Rect(
        SCREEN_WIDTH // 2 - 205, SCREEN_HEIGHT // 2 + 150, 410, 90
    )

    image_dir = os.path.join(BASE_DIR, "image")
    try:
        background = load_image(os.path.join(image_dir, "background.png"))
        lobby_background = load_image(
            os.path.join(image_dir, "game_enter_background.png")
        )
    except (pygame.error, OSError) as exc:
        pygame.quit()
        raise SystemExit(
            f"배경 이미지를 불러오지 못했습니다.\n"
            f"image 폴더와 파일 이름을 확인하세요.\n세부 오류: {exc}"
        )

    # 이미지가 화면 크기와 다르더라도 매 프레임 확대/축소하지 않도록 시작 시 처리
    if background.get_size() != screen.get_size():
        background = pygame.transform.smoothscale(background, screen.get_size())
    if lobby_background.get_size() != screen.get_size():
        lobby_background = pygame.transform.smoothscale(
            lobby_background, screen.get_size()
        )

    # -------------------------------------------------
    # 변수 정의(서버 기본 변수, 내부 사용 변수) 및 서버 시작
    # -------------------------------------------------

    uri = f"ws://{HOST}:{PORT}"
    try:
        async with websockets.connect(
            uri,
            open_timeout=8,
            close_timeout=2,
            ping_interval=20,
            ping_timeout=20,
            max_size=1_000_000,
        ) as websocket:
            incoming = asyncio.Queue()
            receiver = asyncio.create_task(receive_messages(websocket, incoming))

            running = True
            show_name_screen = True
            input_active = False
            nickname = ""
            editing_text = ""
            status_message = "서버에 연결되었습니다."

            try:
                # -------------------------------------------------
                # 이벤트 관리 및 서버 수신, 전송
                # -------------------------------------------------

                while running:
                    # 네트워크 메시지는 이미 별도 작업이 수신하고 있으므로
                    # 큐에 도착한 메시지만 비차단 방식으로 꺼냄
                    while not incoming.empty():
                        message = incoming.get_nowait()
                        if message == "__CONNECTION_CLOSED__":
                            status_message = "서버 연결이 끊어졌습니다."
                        else:
                            status_message = f"서버: {message}"
                            print(f"받은 메시지: {message}")

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False

                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            #---
                            if show_name_screen and name_rect.collidepoint(event.pos):
                                input_active = True
                                pygame.key.start_text_input()
                                pygame.key.set_text_input_rect(name_rect)

                            #---
                            elif show_name_screen and enter_button_rect.collidepoint(event.pos):
                                if nickname.strip():
                                    await websocket.send(f"name,{nickname.strip()}")
                                    input_active = False
                                    pygame.key.stop_text_input()
                                    show_name_screen = False
                                else:
                                    status_message = "닉네임을 입력해주세요."

                            elif not show_name_screen and make_rect.collidepoint(event.pos):
                                await websocket.send("makeroom")
                                status_message = "방 생성 요청을 보냈습니다."

                            elif not show_name_screen and join_rect.collidepoint(event.pos):
                                await websocket.send("enterroom")
                                status_message = "방 입장 요청을 보냈습니다."

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
                                        show_name_screen = False
                                    else:
                                        status_message = "닉네임을 입력해주세요."

                            if event.key == pygame.K_ESCAPE and not show_name_screen:
                                status_message = "ESC를 눌렀습니다."

                    # -------------------------------------------------
                    # 그리기 및 업데이트
                    # -------------------------------------------------

                    # 배경은 한 번 불러온 Surface를 재사용
                    if show_name_screen:
                        screen.blit(background, (0, 0))
                        screen.blit(enter_text, enter_rect)
                        pygame.draw.rect(screen, WHITE, name_rect)

                        display_text = nickname + editing_text
                        name_surface = small_font.render(display_text, True, BLACK)
                        screen.blit(name_surface, (name_rect.x + 10, name_rect.y + 10))

                    else:
                        screen.blit(lobby_background, (0, 0))
                        screen.blit(make_text, make_rect)
                        screen.blit(join_text, join_rect)

                    if status_message:
                        status_surface = small_font.render(status_message, True, WHITE)
                        screen.blit(status_surface, (30, SCREEN_HEIGHT - 30))

                    pygame.display.flip()
                    # tick 자체가 프레임 속도를 제한하므로 별도의 sleep은 제거
                    clock.tick(FPS)
                    await asyncio.sleep(0)

    # -------------------------------------------------
    # 오류
    # -------------------------------------------------

            finally:
                receiver.cancel()
                await asyncio.gather(receiver, return_exceptions=True)
    except (OSError, asyncio.TimeoutError, websockets.exceptions.WebSocketException) as exc:
        print(f"서버 연결 실패: {exc}")
        pygame.quit()
        raise SystemExit(
            f"서버에 연결할 수 없습니다: {uri}\n"
            "서버가 실행 중인지, HOST IP와 포트가 맞는지 확인하세요."
        )

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
