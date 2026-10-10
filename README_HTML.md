# 짭투 HTML 인터페이스 실행 방법

이 버전은 Pygame 화면 대신 HTML/CSS/JavaScript 화면을 사용합니다. `jjaptu_server.py`는 WebSocket 서버로 유지되고, `web_app.py`는 웹 페이지를 제공합니다.

## 1. 설치
```bash
python -m pip install -r requirements-web.txt
```

## 2. 서버 실행
터미널 1에서 프로젝트 폴더로 이동한 뒤 실행합니다.
```bash
python jjaptu_server.py
```

## 3. 웹 화면 실행
터미널 2에서 실행합니다.
```bash
python web_app.py
```
브라우저에서 `http://127.0.0.1:8000`을 엽니다.

## 같은 Wi-Fi의 다른 기기에서 접속
서버 컴퓨터의 사설 IP 주소를 확인한 뒤 다른 기기에서 `http://서버IP:8000`으로 접속합니다. 방화벽에서 TCP 8000 및 WebSocket TCP 65535 연결을 허용해야 할 수 있습니다. HTML은 접속한 주소의 호스트 이름을 사용해 `65535`번 WebSocket 포트에 연결합니다.

## 참고
- `build/web/index.html`, `style.css`, `app.js`가 웹 화면입니다.
- `image/`의 기존 배경 이미지를 `build/web/assets/`로 복사했습니다. 현재 화면은 CSS 기반 디자인이며 이 이미지들은 추후 배경으로 쉽게 적용할 수 있도록 포함했습니다.
- 방 생성, 방 목록, 방 코드 입장, 참가자 목록 업데이트, 방 나가기를 지원합니다. 실제 끝말잇기 턴/단어 검증/게임 시작 로직은 기존 서버에 없으므로 아직 구현되지 않았습니다.
- HTTPS로 배포하는 경우에는 WebSocket도 WSS로 제공되도록 프록시/TLS 설정이 필요합니다.


## 방 생성 라운드 설정

로비에서 `방 만들기`를 누르면 5, 10, 20라운드 중 선택할 수 있습니다. 선택한 값은 `makeroom,<라운드 수>` WebSocket 메시지로 Python 서버에 전달되고, 서버의 방 정보에 저장됩니다. 방 목록과 대기실에는 저장된 라운드 수가 표시되며, 모든 참가자는 같은 설정을 확인할 수 있습니다. 기존 클라이언트와의 호환을 위해 라운드 수가 없는 `makeroom` 요청은 기본값 10라운드로 처리합니다.
