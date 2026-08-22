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

    def makeroom(client_sockets,send_sock):
        for broadcast in client_sockets:
            if broadcast != send_sock:
                try:
                    broadcast.sendto("makeroom".encode('utf-8'),(HOST,POST))
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
                    if data=="makeroom":
                        makeroom(readsocks,sock)
                else:
                    print(f"disconnect:{sock.getpeername()}")
                    readsocks.remove(sock)
                    sock.close()
                    continue
