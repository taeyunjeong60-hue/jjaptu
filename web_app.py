#--------모듈 불러오기--------
from pathlib import Path
from flask import Flask, send_from_directory

#--------경로 및 앱 설정--------
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "build" / "web"
app = Flask(__name__, static_folder=None)

#--------HTML 인터페이스 제공--------
@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")

#--------CSS, JavaScript, 이미지 제공--------
@app.get("/<path:filename>")
def static_files(filename):
    # WebSocket 서버 포트와 HTTP 서버 포트는 별개입니다.
    return send_from_directory(WEB_DIR, filename)

#--------프로그램 시작--------
if __name__ == "__main__":
    print("웹 인터페이스: http://127.0.0.1:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
