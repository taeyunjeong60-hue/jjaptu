#모듈 불러오기
import pygame, socket
import sys
import os

#클라이언트 함수
PORT= 65535
HOST = "172.30.1.73"

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
ge_r=ge.get_rect(center=(screen_width//2,screen_height//2+195))
mr=font.render("방 만들기",True,WHITE)
mr_r=mr.get_rect(center=(150,100))
er=font.render("방 입장",True,WHITE)
er_r=er.get_rect(center=(400,100))

#이미지 불러오기
BASE_DIR=os.path.dirname(__file__)

backgroundimg_path=os.path.join(BASE_DIR,'image','background.png')
game_enter_backgroundimg_path=os.path.join(BASE_DIR,'image','game_enter_background.png')

mbg=pygame.image.load(backgroundimg_path)
gebg=pygame.image.load(game_enter_backgroundimg_path)

#영역 정하기
ni_r=pygame.Rect(screen_width//2-150,screen_height//2+80,300,50)
ge_cr=pygame.Rect(screen_width//2-205,screen_height//2+150,410,90)

#프레임 제작
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s: #서버 입장
    s.connect((HOST,PORT))
    running=True
    show_t=True
    in_r=False
    rooms=[]#방 저장 함수
    
    nickname =""
    #입력이 끝난 글자를 저장 ex)정태
    editing_text=""
    # 아직 조합중인 글자 ex)윤
    input_active = False
    # 지금 이름 입력창에 입력되고 있는지
    s.setblocking(False)
    while running:

        
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False


            # 입력칸 클릭 -> input_active = True -> ㅇㅣ제부터 글자를 nickname
            elif event.type == pygame.MOUSEBUTTONDOWN:

                # 이름 입력창 클릭
                if show_t and ni_r.collidepoint(event.pos):

                    input_active = True

                    pygame.key.start_text_input()
                    pygame.key.set_text_input_rect(ni_r)


                # 입장하기 버튼
                elif show_t and ge_cr.collidepoint(event.pos):

                    if nickname != "":

                        print("닉네임:", nickname)

                        s.send(
                            f"name,{nickname}".encode("utf-8")
                        )

                        input_active = False
                        pygame.key.stop_text_input()

                        show_t = False

                    else:
                        print("이름을 입력해주세요")


                # 방 만들기
                elif not show_t and mr_r.collidepoint(event.pos):

                    s.send(
                        "makeroom".encode("utf-8")
                    )

                    rooms.append(["me"])

                    in_r = True


                # 방 입장
                elif not show_t and er_r.collidepoint(event.pos):

                    s.send(
                        "enterroom".encode("utf-8")
                    )

                    in_r = True


           #한글 조합
            elif event.type == pygame.TEXTEDITING:

                if input_active:
                    editing_text = event.text
                    # nickname=  정


            #문자 입력 완료
            elif event.type == pygame.TEXTINPUT:

                if input_active:

                    if len(nickname) < 10:
                        nickname += event.text

                    editing_text = ""


            #키보드 세티ㅇ
            elif event.type == pygame.KEYDOWN:

                if input_active:

                    # 백스페이스
                    if event.key == pygame.K_BACKSPACE:
                        # ㅈ ㅓ ㅇ ->정
                        # keydown 자연x
                        # 
                        if editing_text == "" and nickname:
                            nickname = nickname[:-1]


                    # 엔터
                    elif event.key == pygame.K_RETURN:

                        if nickname != "":

                            print("닉네임:", nickname)

                            s.send(
                                f"name,{nickname}".encode("utf-8")
                            )

                            input_active = False
                            pygame.key.stop_text_input()

                            show_t = False


                # ESC
                if event.key == pygame.K_ESCAPE:

                    if in_r == False:
                        show_t = True


    

        # 먼저 화면 초기화
        screen.fill(BLACK)


        if show_t:

            # 배경
            screen.blit(
                mbg,
                (0, 0)
            )

            # 입장하기 버튼
            screen.blit(
                ge,
                ge_r
            )

            # 이름 입력창
            pygame.draw.rect(
                screen,
                WHITE,
                ni_r
            )

            # 입력된 이름 + 현재 조합 중 글자
            display_text = nickname + editing_text

            nickname_surface = er_f.render(
                display_text,
                True,
                BLACK
            )

            screen.blit(
                nickname_surface,
                (
                    ni_r.x + 10,
                    ni_r.y + 10
                )
            )


        #방목록
        else:

            screen.blit(
                gebg,
                (0, 0)
            )

            screen.blit(
                mr,
                mr_r
            )


        pygame.display.update()


    pygame.quit()