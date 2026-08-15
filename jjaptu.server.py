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
    
    while True:
        read,write,error=select.select([s],[],[])
        for sock in read:
            if sock==s:#신규 클라이언트 접속
                newsock,addr=s.accept()
                print(f"클라이언트 접속:{newsock,addr}")
                readsocks.append(newsock)
            else:#이미 접속한 클라이언트의 요청
                conn=sock
                data=s.recv(1024).decode("utf-8")
                print(f"데이터:{data}")

