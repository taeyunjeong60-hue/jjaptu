#모듈 불러오기
import pygame, socket
import sys

#클라이언트 함수
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
text=''
eng_kor = {
    'r': 'ㄱ', 'R': 'ㄲ', 's': 'ㄴ', 'e': 'ㄷ', 'E': 'ㄸ',
    'f': 'ㄹ', 'a': 'ㅁ', 'q': 'ㅂ', 'Q': 'ㅃ', 't': 'ㅅ',
    'T': 'ㅆ', 'd': 'ㅇ', 'w': 'ㅈ', 'W': 'ㅉ', 'c': 'ㅊ',
    'z': 'ㅋ', 'x': 'ㅌ', 'v': 'ㅍ', 'g': 'ㅎ',
    'k': 'ㅏ', 'o': 'ㅐ', 'i': 'ㅑ', 'O': 'ㅒ', 'j': 'ㅓ',
    'p': 'ㅔ', 'u': 'ㅕ', 'P': 'ㅖ', 'h': 'ㅗ', 'hk': 'ㅘ',
    'ho': 'ㅙ', 'hl': 'ㅚ', 'y': 'ㅛ', 'n': 'ㅜ', 'nj': 'ㅝ',
    'np': 'ㅞ', 'nl': 'ㅟ', 'b': 'ㅠ', 'm': 'ㅡ', 'ml': 'ㅢ',
    'l': 'ㅣ'
}

def eng_to_kor(text):
    result=''
    for char in text:
        result += eng_kor(char, char)
    return result

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
                    t_input_bool = True
                    
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

            pygame.key.start_text_input()
            
            if t_input_bool:
                if event.type == pygame.KEYDOWN:#텍스트 입력(닉네임)
                
                    if event.key == pygame.K_RETURN:
                        p_name = text
                        text = ''
                        t_input_bool = False
                
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                
                    else:
                        text += event.unicode
                
                    t_font = p_font.render(text, True, BLACK)
                    
            if show_t:#시작 화면 보이기/보이지 않기
                screen.blit(mbg,(0,0))
                screen.blit(ge,(ge_r))
                pygame.draw.rect(screen,WHITE,ni_r)
                screen.blit(t_font,(screen_width//2-150,screen_height//2+80))

            pygame.display.update()

    pygame.quit()
    sys.exit()