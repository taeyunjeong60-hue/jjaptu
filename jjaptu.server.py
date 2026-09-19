#서버
import socket
import select

client_socket=()

HOST=''
POST=65535

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST,POST))
    s.listen()
    print("서버 시작")
    readsocks=[s]
    rooms=[]
    name_dic={}

    def broadcast(client_sockets,send_sock,msg):
        import re
        for broadcast in client_sockets:
            if broadcast != send_sock:
                try:
                    values=re.findall(r"[\d.]+", str(broadcast))
                    print((values[-2],int(values[-1])))
                    broadcast.sendto(f'{msg}{send_sock}'.encode('utf-8'),(values[-2],int(values[-1])))
                except Exception as e:
                    print(f"전송 실패:{e}")

    
    while True:
        read,write,error=select.select(readsocks,[],[])
        for sock in read:
            if sock==s:#신규 클라이언트 접속
                newsock,addr=s.accept()
                print(f"클라이언트 접속:{newsock,addr}")
                readsocks.append(newsock)
            else:#이미 접속한 클라이언트의 요청
                data=sock.recv(1024).decode('utf-8')
                if data:
                    if "name" in data:
                        name=data.split(",")
                        name_dic[sock]=name[1]
                        print(name_dic)

                    elif data=="makeroom":
                        rooms.append([sock])
                        broadcast(readsocks,sock,"makeroom")
                        print(rooms)

                    elif data=="enterroom":
                        rooms[0].append(sock)
                        sock.send("enterroom") 
                else:
                    print(f"disconnect:{sock.getpeername()}")
                    readsocks.remove(sock)
                    sock.close()
                    continue
