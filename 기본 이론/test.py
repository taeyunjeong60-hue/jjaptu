import pygame
import sys

# 1. Pygame 초기화
pygame.init()

# 2. 화면 크기 설정 (가로, 세로) 및 창 생성
SCREEN_WIDTH = 1408
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# 3. 창 제목 설정
pygame.display.set_caption("Pygame 화면 미리보기")

# 4. RGB 색상 정의 (R, G, B)
BACKGROUND_COLOR = (30, 30, 30) # 어두운 회색
WHITE=(0,0,0)

#범위 테스트
test_rect=pygame.Rect(200,200,300,300)
#----------

# 5. 게임 메인 루프
running = True
while running:
    # 6. 이벤트 처리 (마우스, 키보드 입력 등)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: # 창 닫기 버튼을 누르면
            running = False

    # 7. 화면 배경색 채우기
    screen.fill(BACKGROUND_COLOR)

    # 그리기
    pygame.draw.rect(True,WHITE,test_rect)

    # 8. 화면 전체 업데이트 (화면 그리기)
    pygame.display.flip()

# 9. Pygame 종료 및 프로그램 종료
pygame.quit()
sys.exit()
