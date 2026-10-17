# 짭투 베타 - Render 배포 안내

## 1. GitHub 저장소 준비

1. GitHub에서 새 저장소를 만듭니다.
2. ZIP의 바깥쪽 `jjaptu` 폴더 안에 있는 파일과 폴더를 저장소 루트에 올립니다. `render.yaml`, `web_app.py`, `jjaptu_server.py`, `requirements-web.txt`, `build/`가 저장소 최상위에 있어야 합니다.
3. `.env` 파일은 올리지 마세요. `.gitignore`에서 제외하도록 설정되어 있습니다.

## 2. Render 배포

1. Render Dashboard에서 **New + → Blueprint**를 선택합니다.
2. GitHub 저장소를 연결하고 `render.yaml`을 선택해 배포를 시작합니다.
3. 또는 **New + → Web Service**로 생성하고 다음 값을 사용합니다.
   - Build Command: `pip install -r requirements-web.txt`
   - Start Command: `python web_app.py`
   - Health Check Path: `/healthz`
   - Region: Singapore
   - Instance: Free (베타 테스트용)
4. 배포가 완료되면 Render가 제공하는 `https://...onrender.com` 주소를 엽니다. WebSocket 주소는 자동으로 같은 도메인의 `/ws` 경로를 사용합니다.

## 3. 표준국어대사전 API 키 (선택 사항)

API 키는 GitHub 파일이나 소스 코드에 적지 마세요. Render Dashboard에서 해당 서비스의 **Environment**에 다음 변수를 추가합니다.

- Key: `KOREAN_DICT_API_KEY`
- Value: 발급받은 표준국어대사전 API 키

저장 후 재배포합니다. API 키를 설정하지 않으면 게임은 데모 검증 모드로 실행되어 자음·모음 조건만 검사합니다.

로컬에서 실행할 때는 프로젝트 폴더의 `.env` 파일에 `KOREAN_DICT_API_KEY=실제키` 형식으로 저장할 수 있습니다. `.env`는 비밀값이므로 GitHub에 커밋하지 마세요.

## 4. 베타 운영 시 주의 사항

- 방 목록과 점수는 현재 메모리에 저장되므로 서버가 재시작되면 초기화됩니다.
- 이 버전은 한 개의 서버 인스턴스로 운영하세요. 인스턴스를 여러 개 띄우면 각 인스턴스의 방 목록이 서로 달라집니다.
- Render 무료 서비스는 유휴 시간 후 잠들 수 있어 첫 접속이 느릴 수 있습니다.
- 배포 후 두 개의 브라우저/기기에서 서로 다른 닉네임으로 접속해 방 생성, 참가, 게임 시작, 정답 제출을 테스트하세요.
