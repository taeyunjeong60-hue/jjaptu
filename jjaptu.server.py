#서버
import socket

client_socket=()

HOST=''
POST=65535

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST,POST))
    s.listen()
    print("서버 시작")
    while True:
        conn,addr=s.accept()    
    

    
