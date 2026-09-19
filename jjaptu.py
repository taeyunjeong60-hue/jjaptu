#모듈 불러오기
import pygame, socket
import sys
import flask import url_for

#클라이언트 함수
HOST='192.168.0.37'
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

pygame.key.start_text_input()
pygame.init()
pygame.time.Clock()

#폰트 정하기&글자 정하기
p_font=pygame.font.SysFont("malgungothic", 30)
font=pygame.font.SysFont("malgungothic", 40)
er_f=pygame.font.SysFont("malgungothic", 20)

ge=font.render("입장하기",True,DARKGRAY)
ge_r=ge.get_rect(center=(screen_width//2,screen_height//2+195))
mr=font.render("방 만들기",True,WHITE)
mr_r=mr.get_rect(center=(150,100))
er=font.render("방 입장",True,WHITE)
er_r=er.get_rect(center=(400,100))
t_font = p_font.render("이름 입력", True, BLACK)

#이미지 불러오기
mbg=pygame.image.load("C:/Users/APP_6/Desktop/정태윤/jjaptu/이미지 모음/background.png")
gebg=pygame.image.load("C:/Users/APP_6/Desktop/정태윤/jjaptu/이미지 모음/game_enter_background.png")

#영역 정하기
ni_r=pygame.Rect(screen_width//2-150,screen_height//2+80,300,50)
ge_cr=pygame.Rect(screen_width//2-205,screen_height//2+150,410,90)

#한국어 입력
class InputField:
    def __init__(self, size) -> None:
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 255))
        self.font = pygame.font.SysFont("malgungothic", size[1])
        self.text = ""
        self.edit_pos = 0
        self.text_edit = False
        self.text_editing = ""
        
    def event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:self.edit_pos-1] + self.text[self.edit_pos:]
                self.edit_pos = max(0, self.edit_pos-1)
        elif event.type == pygame.TEXTEDITING:
            self.text_edit = True
            self.text_editing = event.text
            self.text_editing_pos = event.start
        elif event.type == pygame.TEXTINPUT:
            self.text_edit = False
            self.text_editing = ""
            self.text = self.text[:self.edit_pos] + event.text + self.text[self.edit_pos:]
            self.edit_pos = min(self.edit_pos + len(event.text), len(self.text + self.text_editing))
                
    def render(self, surface):
        surface.blit(self.image, self.image.get_rect(topleft=(200, 500)))
        string = self.font.render(self.text + self.text_editing, True, (255, 255, 255))
        surface.blit(string, string.get_rect(topleft=(200, 500)))

input_field=InputField((300,30))

#프레임 제작
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s: #서버 입장
    s.connect((HOST,PORT))
    
    running=True
    show_t=True
    in_r=False
    t_input_bool=False
    rooms=[]#방 저장 함수
    s.setblocking(False)
    while running:

        #데이터 받기
        try:
            data=s.recv(1024).decode('utf-8')

            if data:
                if data=="makeroom":#방 만들기
                    screen.blit(er,(er_r))
        except BlockingIOError:
            pass

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False        

            #클릭 이벤트 감지
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if show_t and ni_r.collidepoint(event.pos):#이름 입력 상자 클릭
                    text=''
                    t_font = p_font.render(text, True, BLACK)
                    t_input_bool=True
                
                if show_t and ge_cr.collidepoint(event.pos):#입장 버튼
                    show_t=False
                    screen.blit(gebg,(0,0))
                    screen.blit(mr,(mr_r))
               
                if mr_r.collidepoint(event.pos):#방 만들기 버튼
                    s.send("makeroom".encode('utf-8'))
                    rooms.append(["me"])
                    in_r=True

                if er_r.collidepoint(event.pos):#방 입장 버튼
                    s.send("enterroom".encode('utf-8'))
                    in_r=True

            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE and in_r==False:#esc버튼 누를 시 메인화면
                    show_t=True

            

            if t_input_bool:
                if event.type==pygame.KEYDOWN:
                    InputField.event(event)

            input_field.render(screen)

            if show_t:#시작 화면 보이기/보이지 않기
                screen.blit(mbg,(0,0))
                screen.blit(ge,(ge_r))
                pygame.draw.rect(screen,WHITE,ni_r)
                screen.blit(t_font,(screen_width//2-150,screen_height//2+80))

            pygame.display.update()

    pygame.quit()
    sys.exit()