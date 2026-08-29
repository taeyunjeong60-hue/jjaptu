#모듈 불러오기
import pygame, socket
import sys

#클라이언트 함수
HOST='172.30.1.73'
PORT= 65535

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
font=pygame.font.SysFont("malgungothic", 40)
er_f=pygame.font.SysFont("malgungothic", 20)

ge=font.render("입장하기",True,DARKGRAY)
ge_r=ge.get_rect(center=(screen_width//2,screen_height//2+145))
mr=font.render("방 만들기",True,WHITE)
mr_r=mr.get_rect(center=(150,100))
er=font.render("방 입장",True,WHITE)
er_r=er.get_rect(center=(400,100))

#이미지 불러오기
mbg=pygame.image.load("C:/Users/APP_1/Desktop/정태윤/pythoncert/game_s/jjaptu/이미지 모음/background.png")
gebg=pygame.image.load("C:/Users/APP_1/Desktop/정태윤/pythoncert/game_s/jjaptu/이미지 모음/game_enter_background.png")

#영역 정하기
ge_cr=pygame.Rect(screen_width//2-205,screen_height//2+45,410,200)

#프레임 제작
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s: #서버 입장
    s.connect((HOST,PORT))
    running=True
    show_t=True
    s.setblocking(False)
    while running:

        try:
            data=s.recv(1024).decode('utf-8')

            if data:
                if data=="makeroom":
                    screen.blit(er,(er_r))
        except BlockingIOError:
            pass

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False        

            if event.type == pygame.MOUSEBUTTONDOWN:
                if show_t and ge_cr.collidepoint(event.pos):
                    show_t=False
                    screen.blit(gebg,(0,0))
                    screen.blit(mr,(mr_r))
               
                if mr_r.collidepoint(event.pos):
                    s.send("makeroom".encode('utf-8'))

                    
            if show_t:
                screen.blit(mbg,(0,0))
                screen.blit(ge,(ge_r))

            pygame.display.update()

    pygame.quit()
    sys.exit()