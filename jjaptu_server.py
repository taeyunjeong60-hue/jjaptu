#--------모듈 불러오기--------
import asyncio
import json
import secrets
import os
import re
import random
from pathlib import Path
import requests
import websockets
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

#--------서버 연결 설정--------
HOST = ""
PORT = 65535

#--------접속자 및 방 정보 저장 공간--------
connected_clients = set()
name_dic = {}
rooms = {}  # room_id: {"owner": websocket, "members": [websocket]}

KOREAN_CON = ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
KOREAN_VOWELS = ["ㅏ", "ㅑ", "ㅓ", "ㅕ", "ㅗ", "ㅛ", "ㅜ", "ㅠ", "ㅡ", "ㅣ", "ㅐ", "ㅒ", "ㅔ", "ㅖ", "ㅘ", "ㅙ", "ㅚ", "ㅝ", "ㅞ", "ㅟ", "ㅢ"]
INITIALS = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
VOWELS = ["ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ", "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ"]
FINAL_CONS = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
GAME_LOCK = asyncio.Lock()
ROUND_SECONDS = 30

def split_hangul(word):
    """완성형 한글 음절을 초성/중성/종성으로 분해합니다."""
    parts = []
    for char in word:
        code = ord(char) - 0xAC00
        if 0 <= code <= 11171:
            initial = code // 588
            vowel = (code % 588) // 28
            final = code % 28
            parts.append((INITIALS[initial], VOWELS[vowel], FINAL_CONS[final]))
    return parts

def word_matches_prompt(word, consonant, vowel):
    parts = split_hangul(word)
    return any(initial == consonant for initial, _, _ in parts) and any(middle == vowel for _, middle, _ in parts)

def dictionary_lookup(word):
    """국립국어원 표준국어대사전 API로 단어를 확인합니다. 키가 없으면 None을 반환합니다."""
    api_key = os.getenv("KOREAN_DICT_API_KEY", "").strip()
    if not api_key:
        return None
    response = requests.get(
        "https://stdict.korean.go.kr/api/search.do",
        params={"key": api_key, "q": word, "req_type": "json", "num": 100},
        timeout=6,
    )
    response.raise_for_status()
    data = response.json() if response.text.strip() else {}
    channel = data.get("channel", {}) if isinstance(data, dict) else {}
    items = channel.get("item", []) if isinstance(channel, dict) else []
    if isinstance(items, dict):
        items = [items]
    for item in items or []:
        if not isinstance(item, dict):
            continue
        found = str(item.get("word", "")).strip()
        # 사전의 동형어 번호나 표시용 기호는 비교에서 제외합니다.
        found_clean = re.sub(r"[^가-힣]", "", found)
        if found_clean == word:
            return True
    return False

def make_prompt():
    return {"consonant": random.choice(KOREAN_CON), "vowel": random.choice(KOREAN_VOWELS)}

#--------닉네임 조회 함수--------
def nickname_of(client):
    return name_dic.get(client, "알 수 없음")

#--------방 정보 구성 함수--------
def room_payload(room_id, kind="room_update", viewer=None):
    room = rooms[room_id]
    return {
        "type": kind,
        "room_id": room_id,
        "owner": nickname_of(room["owner"]),
        # 각 클라이언트가 본인이 방장인지 서버에서 확정해 전달합니다.
        "is_owner": viewer is not None and room["owner"] is viewer,
        "members": [nickname_of(member) for member in room["members"]],
        "rounds": room.get("rounds", 10),
        "max_players": room.get("max_players", 8),
        "game_active": bool(room.get("game", {}).get("active", False)),
    }

#--------JSON 메시지 전송 함수--------
async def send_json(client, payload):
    await client.send(json.dumps(payload, ensure_ascii=False))

#--------전체 방 목록 전송 함수--------
async def send_room_list(client):
    items = []
    for room_id, room in rooms.items():
        items.append({
            "room_id": room_id,
            "owner": nickname_of(room["owner"]),
            "members_count": len(room["members"]),
            "rounds": room.get("rounds", 10),
            "max_players": room.get("max_players", 8),
        })
    await send_json(client, {"type": "room_list", "rooms": items})

async def broadcast_room_list():
    clients = list(connected_clients)
    if clients:
        results = await asyncio.gather(*(send_room_list(c) for c in clients), return_exceptions=True)
        for client, result in zip(clients, results):
            if isinstance(result, Exception):
                print(f"방 목록 전송 실패: {result}")

#--------방 참가자에게 최신 방 정보 전송--------
async def broadcast_room(room_id):
    room = rooms.get(room_id)
    if not room:
        return
    clients = list(room["members"])
    # is_owner는 참가자마다 달라서 클라이언트별로 별도 전송합니다.
    payloads = [
        json.dumps(room_payload(room_id, viewer=client), ensure_ascii=False)
        for client in clients
    ]
    results = await asyncio.gather(
        *(client.send(payload) for client, payload in zip(clients, payloads)),
        return_exceptions=True
    )
    for client, result in zip(clients, results):
        if isinstance(result, Exception):
            print(f"방 정보 전송 실패({room_id}): {result}")

#--------방에서 나가기 처리--------
async def leave_room(client, notify=True):
    for room_id in list(rooms):
        room = rooms[room_id]
        if client not in room["members"]:
            continue
        room["members"].remove(client)
        game = room.get("game")
        if game and isinstance(game.get("scores"), dict):
            game["scores"].pop(client, None)
        if not room["members"]:
            del rooms[room_id]
            print(f"빈 방 삭제: {room_id}")
        else:
            if room["owner"] is client:
                room["owner"] = room["members"][0]
            await broadcast_room(room_id)
        if notify and client in connected_clients:
            await send_json(client, {"type": "room_left"})
        await broadcast_room_list()
        return

#--------게임 진행 보조 함수--------
async def broadcast_game(room_id, payload):
    room = rooms.get(room_id)
    if not room:
        return
    message = json.dumps(payload, ensure_ascii=False)
    await asyncio.gather(*(member.send(message) for member in list(room["members"])), return_exceptions=True)

async def finish_game(room_id):
    room = rooms.get(room_id)
    if not room:
        return
    game = room.get("game")
    if not game or not game.get("active"):
        return
    game["active"] = False
    scores = [{"nickname": nickname_of(member), "score": score} for member, score in game["scores"].items()]
    scores.sort(key=lambda row: (-row["score"], row["nickname"]))
    await broadcast_game(room_id, {"type": "game_over", "scores": scores, "round": game["round"], "rounds": game["rounds_total"]})
    print(f"게임 종료: 방={room_id}")

async def advance_round(room_id, expected_round=None):
    room = rooms.get(room_id)
    if not room:
        return
    game = room.get("game")
    if not game or not game.get("active"):
        return
    if expected_round is not None and game["round"] != expected_round:
        return
    if game["round"] >= game["rounds_total"]:
        await finish_game(room_id)
        return
    game["round"] += 1
    game["surrendered"] = set()
    game["prompt"] = make_prompt()
    game["round_started_at"] = asyncio.get_running_loop().time()
    await broadcast_game(room_id, {
        "type": "game_round", "room_id": room_id, "round": game["round"],
        "rounds": game["rounds_total"], "consonant": game["prompt"]["consonant"],
        "vowel": game["prompt"]["vowel"], "seconds": ROUND_SECONDS,
        "scores": [{"nickname": nickname_of(member), "score": score} for member, score in game["scores"].items()],
    })
    asyncio.create_task(round_timeout(room_id, game["round"]))

async def round_timeout(room_id, expected_round):
    await asyncio.sleep(ROUND_SECONDS)
    room = rooms.get(room_id)
    if not room:
        return
    game = room.get("game")
    if not game or not game.get("active") or game.get("round") != expected_round:
        return
    await broadcast_game(room_id, {"type": "round_timeout", "round": expected_round, "message": "시간이 끝났습니다. 다음 라운드로 넘어갑니다."})
    await advance_round(room_id, expected_round)

#--------클라이언트 요청 처리 함수--------
async def handler(websocket):
    connected_clients.add(websocket)
    print(f"접속: {websocket.remote_address} / 접속자 {len(connected_clients)}명")
    await send_room_list(websocket)
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                message = message.decode("utf-8", errors="replace")
            print(f"클라이언트 메시지: {message}")

            #--------닉네임 등록--------
            if message.startswith("name,"):
                nickname = message.partition(",")[2].strip()[:10]
                if not nickname:
                    await send_json(websocket, {"type": "error", "code": "invalid_nickname", "message": "닉네임을 입력해주세요."})
                    continue

                # 접속 중인 다른 플레이어와 닉네임이 겹치는지 확인합니다.
                # 영문 대소문자만 다른 이름도 중복으로 처리합니다.
                nickname_key = nickname.casefold()
                name_taken = any(
                    client is not websocket and existing_name.casefold() == nickname_key
                    for client, existing_name in name_dic.items()
                )
                if name_taken:
                    await send_json(websocket, {
                        "type": "error",
                        "code": "nickname_taken",
                        "message": f"'{nickname}'은(는) 이미 사용 중인 이름입니다. 다른 이름을 입력해주세요."
                    })
                    continue

                name_dic[websocket] = nickname
                await send_json(websocket, {"type": "name_ok", "nickname": nickname})
                # 닉네임 변경 시 방 목록과 현재 방 참가자 표시도 갱신합니다.
                await broadcast_room_list()
                for room_id, room in list(rooms.items()):
                    if websocket in room["members"]:
                        await broadcast_room(room_id)

            #--------방 생성--------
            elif message == "makeroom" or message.startswith("makeroom,"):
                if not name_dic.get(websocket):
                    await send_json(websocket, {"type": "error", "message": "먼저 닉네임을 등록해주세요."})
                    continue

                # 서버 전체 방 개수 제한: 최대 100개
                if len(rooms) >= 100:
                    await send_json(websocket, {"type": "error", "code": "rooms_full", "message": "현재 생성 가능한 방이 100개로 가득 찼습니다. 잠시 후 다시 시도해주세요."})
                    continue

                #--------방 생성 설정 검증--------
                parts = message.split(",")
                try:
                    rounds = int(parts[1]) if len(parts) > 1 else 10
                    max_players = int(parts[2]) if len(parts) > 2 else 8
                except ValueError:
                    rounds, max_players = 0, 0
                if rounds not in {5, 10, 20}:
                    await send_json(websocket, {"type": "error", "message": "라운드 수는 5, 10, 20 중에서 선택해주세요."})
                    continue
                if max_players not in {2, 4, 6, 8, 10}:
                    await send_json(websocket, {"type": "error", "message": "최대 인원은 2, 4, 6, 8, 10명 중에서 선택해주세요."})
                    continue

                await leave_room(websocket, notify=False)
                room_id = secrets.token_hex(3).upper()
                while room_id in rooms:
                    room_id = secrets.token_hex(3).upper()
                rooms[room_id] = {
                    "owner": websocket,
                    "members": [websocket],
                    "rounds": rounds,
                    "max_players": max_players,
                }
                await send_json(websocket, room_payload(room_id, "makeroom_ok", websocket))
                await broadcast_room_list()
                print(f"방 생성: ID={room_id}, 방장={nickname_of(websocket)}, 라운드={rounds}, 최대 인원={max_players}")

            #--------방 설정 변경(방장 전용)--------
            elif message.startswith("setroomsettings,"):
                parts = message.split(",")
                if len(parts) != 3:
                    await send_json(websocket, {"type": "error", "message": "방 설정 형식이 올바르지 않습니다."})
                    continue
                room_id = next((rid for rid, room in rooms.items() if websocket in room["members"]), None)
                if room_id is None:
                    await send_json(websocket, {"type": "error", "message": "먼저 방에 입장해주세요."})
                    continue
                room = rooms[room_id]
                if room["owner"] is not websocket:
                    await send_json(websocket, {"type": "error", "code": "owner_only", "message": "방장만 방 설정을 변경할 수 있습니다."})
                    continue
                try:
                    rounds = int(parts[1])
                    max_players = int(parts[2])
                except ValueError:
                    rounds, max_players = 0, 0
                if rounds not in {5, 10, 20} or max_players not in {2, 4, 6, 8, 10}:
                    await send_json(websocket, {"type": "error", "message": "선택한 방 설정이 올바르지 않습니다."})
                    continue
                if max_players < len(room["members"]):
                    await send_json(websocket, {"type": "error", "message": f"현재 참가자가 {len(room['members'])}명이므로 최대 인원을 그보다 적게 설정할 수 없습니다."})
                    continue
                room["rounds"] = rounds
                room["max_players"] = max_players
                await broadcast_room(room_id)
                await broadcast_room_list()
                await send_json(websocket, {"type": "room_settings_ok", "message": "방 설정을 변경했습니다."})

            #--------게임 시작(방장 전용)--------
            elif message == "startgame":
                room_id = next((rid for rid, room in rooms.items() if websocket in room["members"]), None)
                if room_id is None:
                    await send_json(websocket, {"type": "error", "message": "먼저 방에 입장해주세요."})
                    continue
                room = rooms[room_id]
                if room["owner"] is not websocket:
                    await send_json(websocket, {"type": "error", "code": "owner_only", "message": "방장만 게임을 시작할 수 있습니다."})
                    continue
                if room.get("game", {}).get("active"):
                    await send_json(websocket, {"type": "error", "message": "이미 게임이 진행 중입니다."})
                    continue
                scores = {member: 0 for member in room["members"]}
                room["game"] = {
                    "active": True,
                    "round": 0,
                    "rounds_total": room.get("rounds", 10),
                    "scores": scores,
                    "used_words": set(),
                    "prompt": None,
                }
                await broadcast_game(room_id, {"type": "game_started", "room_id": room_id, "rounds": room["game"]["rounds_total"], "seconds": ROUND_SECONDS, "message": "게임이 시작되었습니다!"})
                await advance_round(room_id)

            #--------단어 제출--------
            elif message.startswith("submitword,"):
                word = message.partition(",")[2].strip().replace(" ", "")
                room_id = next((rid for rid, room in rooms.items() if websocket in room["members"]), None)
                if room_id is None:
                    await send_json(websocket, {"type": "error", "message": "먼저 게임 방에 입장해주세요."})
                    continue
                async with GAME_LOCK:
                    room = rooms.get(room_id)
                    game = room.get("game") if room else None
                    if not game or not game.get("active"):
                        await send_json(websocket, {"type": "word_result", "ok": False, "message": "현재 진행 중인 게임이 없습니다."})
                        continue
                    if websocket in game.get("surrendered", set()):
                        await send_json(websocket, {
                            "type": "word_result",
                            "ok": False,
                            "message": "이번 라운드에서 기권했으므로 제출할 수 없습니다."
                        })
                        continue
                    if websocket not in game["scores"]:
                        game["scores"][websocket] = 0
                    if not re.fullmatch(r"[가-힣]{2,20}", word):
                        await send_json(websocket, {"type": "word_result", "ok": False, "message": "단어는 한글 2~20자로 입력해주세요."})
                        continue
                    if word in game["used_words"]:
                        await send_json(websocket, {"type": "word_result", "ok": False, "message": "이번 게임에서 이미 나온 단어입니다."})
                        continue
                    prompt = game["prompt"] or {}
                    consonant, vowel = prompt.get("consonant"), prompt.get("vowel")
                    if not word_matches_prompt(word, consonant, vowel):
                        await send_json(websocket, {"type": "word_result", "ok": False, "message": f"'{consonant}' 자음과 '{vowel}' 모음이 모두 들어간 단어를 입력해주세요."})
                        continue
                    try:
                        dictionary_result = await asyncio.to_thread(dictionary_lookup, word)
                    except requests.RequestException:
                        await send_json(websocket, {"type": "word_result", "ok": False, "message": "국어사전 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요."})
                        continue
                    except (ValueError, TypeError, json.JSONDecodeError):
                        await send_json(websocket, {"type": "word_result", "ok": False, "message": "국어사전 응답을 읽지 못했습니다. API 키를 확인해주세요."})
                        continue
                    if dictionary_result is False:
                        await send_json(websocket, {"type": "word_result", "ok": False, "message": "표준국어대사전에서 찾을 수 없는 단어입니다."})
                        continue
                    # API 키가 없으면 데모 모드로 글자 조건만 검사합니다.
                    fallback_mode = dictionary_result is None
                    game["used_words"].add(word)
                    points = 10 + min(len(word), 10)
                    game["scores"][websocket] = game["scores"].get(websocket, 0) + points
                    await broadcast_game(room_id, {
                        "type": "word_accepted", "nickname": nickname_of(websocket), "word": word,
                        "points": points, "round": game["round"], "score": game["scores"][websocket],
                        "fallback_mode": fallback_mode,
                        "message": (f"{nickname_of(websocket)}님이 '{word}'을(를) 맞혔습니다! +{points}점" + (" (데모 검증)" if fallback_mode else "")),
                        "scores": [{"nickname": nickname_of(member), "score": score} for member, score in game["scores"].items()],
                    })
                    # 첫 정답자만 점수를 얻고 즉시 다음 라운드로 넘어갑니다.
                    await advance_round(room_id, game["round"])

                        #--------현재 라운드 기권--------
            elif message == "surrender":
                room_id = next(
                    (
                        rid for rid, room in rooms.items()
                        if websocket in room["members"]
                    ),
                    None
                )

                if room_id is None:
                    await send_json(websocket, {
                        "type": "error",
                        "message": "먼저 게임 방에 입장해주세요."
                    })
                    continue

                async with GAME_LOCK:
                    room = rooms.get(room_id)
                    game = room.get("game") if room else None

                    if not game or not game.get("active"):
                        await send_json(websocket, {
                            "type": "error",
                            "message": "현재 진행 중인 게임이 없습니다."
                        })
                        continue

                    if websocket not in game.get("scores", {}):
                        await send_json(websocket, {
                            "type": "error",
                            "message": "현재 라운드에 참가할 수 없습니다."
                        })
                        continue

                    surrendered = game.setdefault("surrendered", set())

                    if websocket in surrendered:
                        await send_json(websocket, {
                            "type": "error",
                            "message": "이미 이번 라운드에서 기권했습니다."
                        })
                        continue

                    surrendered.add(websocket)

                    participants = [
                        member for member in room["members"]
                        if member in game["scores"]
                    ]

                    surrendered_nicknames = [
                        nickname_of(member)
                        for member in participants
                        if member in surrendered
                    ]

                    await broadcast_game(room_id, {
                        "type": "surrender_update",
                        "surrendered_nicknames": surrendered_nicknames,
                        "surrendered_count": len(surrendered_nicknames),
                        "total_players": len(participants),
                        "message": (
                            f"{nickname_of(websocket)}님이 기권했습니다. "
                            f"({len(surrendered_nicknames)}/{len(participants)}명)"
                        ),
                    })

                    # 모든 현재 참가자가 기권했을 때만 라운드를 종료합니다.
                    if participants and all(
                        member in surrendered for member in participants
                    ):
                        expected_round = game["round"]

                        await broadcast_game(room_id, {
                            "type": "round_timeout",
                            "round": expected_round,
                            "message": "모든 참가자가 기권했습니다. 다음 라운드로 넘어갑니다."
                        })

                        await advance_round(room_id, expected_round)
            
            #--------방 목록 요청--------
            elif message == "listrooms":
                await send_room_list(websocket)

            #--------특정 방 입장--------
            elif message.startswith("joinroom,") or message == "enterroom":
                if not name_dic.get(websocket):
                    await send_json(websocket, {"type": "error", "message": "먼저 닉네임을 등록해주세요."})
                    continue
                if message.startswith("joinroom,"):
                    room_id = message.partition(",")[2].strip().upper()
                else:
                    room_id = next(iter(rooms), "")
                if not room_id or room_id not in rooms:
                    await send_json(websocket, {"type": "error", "message": "입장 가능한 방이 없습니다."})
                    continue
                room = rooms[room_id]
                if websocket not in room["members"] and len(room["members"]) >= room.get("max_players", 8):
                    await send_json(websocket, {"type": "error", "code": "room_full", "message": "이 방은 인원이 가득 찼습니다."})
                    continue
                await leave_room(websocket, notify=False)
                room = rooms.get(room_id)
                if room is None:
                    await send_json(websocket, {"type": "error", "message": "해당 방이 이미 사라졌습니다."})
                    continue
                if websocket not in room["members"]:
                    if len(room["members"]) >= room.get("max_players", 8):
                        await send_json(websocket, {"type": "error", "code": "room_full", "message": "이 방은 인원이 가득 찼습니다."})
                        continue
                    room["members"].append(websocket)
                await send_json(websocket, room_payload(room_id, "room_joined", websocket))
                await broadcast_room(room_id)
                await broadcast_room_list()

            #--------방 나가기--------
            elif message == "leaveroom":
                await leave_room(websocket)

            else:
                await send_json(websocket, {"type": "error", "message": "알 수 없는 요청입니다."})

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await leave_room(websocket, notify=False)
        connected_clients.discard(websocket)
        name_dic.pop(websocket, None)
        await broadcast_room_list()
        print(f"연결 종료: {websocket.remote_address} / 접속자 {len(connected_clients)}명")

#--------WebSocket 서버 실행 함수--------
async def main():
    async with websockets.serve(handler, HOST, PORT, ping_interval=20, ping_timeout=20, max_size=1_000_000):
        print(f"WebSocket 서버 시작: {HOST or '0.0.0.0'}:{PORT}")
        await asyncio.Future()

#--------프로그램 시작--------
if __name__ == "__main__":
    asyncio.run(main())
