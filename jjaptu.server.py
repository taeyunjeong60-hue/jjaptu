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
            conn,addr=s.accept()    
        
    

    
