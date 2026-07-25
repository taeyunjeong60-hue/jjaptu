#모듈 불러오기
import pygame, socket
import sys

#클라이언트 함수
HOST='localhost'
PORT= 65535

with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    s.connect((HOST,PORT))

#색깔 정의
WHITEGRAY=(100,100,100)
DARKGRAY=(30,30,30)
WHITE=(255,255,255)
BLACK=(0,0,0)

#창 크기 정하기
screen_width=1408
screen_height=768
screen=pygame.display.set_mode((screen_width,screen_height))

pygame.init()
pygame.time.Clock()

#폰트 정하기&글자 정하기
game_enter_font=pygame.font.SysFont("malgungothic", 40)

game_enter=game_enter_font.render("입장하기",True,DARKGRAY)
game_enter_rect=game_enter.get_rect(center=(screen_width//2,screen_height//2+145))
make_room=game_enter_font.render("방 만들기",True,WHITE)
make_room_rect=make_room.get_rect(center=(150,100))

#이미지 불러오기
background=pygame.image.load("C:/Users/APP_1/Desktop/정태윤/pythoncert/game_s/짭투 개발/이미지 모음/background.png")
game_enter_background=pygame.image.load("C:/Users/APP_1/Desktop/정태윤/pythoncert/game_s/짭투 개발/이미지 모음/game_enter_background.png")

#영역 정하기
game_enter_click_rect=pygame.Rect(screen_width//2-205,screen_height//2+45,410,200)

#프레임 제작
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s: #서버 입장
    s.connect((HOST,PORT))
    running=True
    show_thumbscreen=True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False        

            if event.type == pygame.MOUSEBUTTONDOWN:
                if show_thumbscreen and game_enter_click_rect.collidepoint(event.pos):
                    show_thumbscreen=False
                    screen.blit(game_enter_background,(0,0))
                    screen.blit(make_room,(make_room_rect))
                
                if make_room_rect.collidepoint(event.pos):
                    s.send("makeroom".encode("utf-8"))
                    
            if show_thumbscreen:
                screen.blit(background,(0,0))
                screen.blit(game_enter,(game_enter_rect))

            pygame.display.update()

    pygame.quit()
    sys.exit()