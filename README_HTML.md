# 짭투 웹 버전 실행 안내

이 프로젝트는 HTML/CSS/JavaScript 화면과 Python WebSocket 게임 서버를 `web_app.py`에서 함께 실행합니다.

## 설치 및 실행

```bash
python -m pip install -r requirements-web.txt
python web_app.py
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다. 기본 포트는 8000이며, Render에서는 `PORT` 환경 변수를 자동으로 사용합니다. 웹 화면은 같은 도메인의 `/ws` 경로로 WebSocket에 연결합니다.

## API 키 설정

선택 사항입니다. `.env.example`을 복사해 `.env`로 이름을 바꾸고 `KOREAN_DICT_API_KEY`에 API 키를 입력하세요. Render에서는 Dashboard의 서비스 **Environment**에 같은 이름의 환경 변수를 등록합니다. 실제 `.env` 파일은 GitHub에 올리지 마세요.

## 배포

Render 배포는 `README_RENDER.md`를 참고하세요.

## 참고

- `build/web/`에는 웹 페이지에 필요한 HTML, CSS, JavaScript만 포함되어 있습니다.
- `image/`는 기존 Pygame 클라이언트가 사용하는 배경 이미지입니다.
- `.venv/`, `.git/`, Python 캐시 및 실험용 파일은 배포용 ZIP에서 제외했습니다.
