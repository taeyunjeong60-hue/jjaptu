//--------WebSocket 연결 설정--------
const WS_PORT = 65535;
const WS_PROTOCOL = location.protocol === 'https:' ? 'wss:' : 'ws:';
const socketUrl = `${WS_PROTOCOL}//${location.hostname}:${WS_PORT}`;
let socket;
let nickname = '';
let currentRoomId = '';
let currentRoomOwner = '';
let currentIsOwner = false;
let currentMembers = [];
let currentRounds = 10;
let currentMaxPlayers = 8;
let roomList = [];
let toastTimer;
let gameTimerInterval = null;
let gameRoundSeconds = 30;
let gameEndsAt = 0;
let gameActive = false;

//--------화면 요소--------
const $ = (id) => document.getElementById(id);
const pages = { nickname: $('nicknamePage'), lobby: $('lobbyPage'), room: $('roomPage'), game: $('gamePage') };
function showPage(name) {
  Object.entries(pages).forEach(([key, node]) => node.classList.toggle('hidden', key !== name));
}
function toast(message) {
  const node = $('toast'); node.textContent = message; node.classList.add('show');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => node.classList.remove('show'), 2800);
}
function send(message) {
  if (!socket || socket.readyState !== WebSocket.OPEN) { toast('서버에 연결되어 있지 않습니다.'); return false; }
  socket.send(message); return true;
}

//--------서버 연결 및 메시지 처리--------
function connect() {
  try { socket = new WebSocket(socketUrl); }
  catch (error) { setConnection(false); toast('WebSocket 연결을 시작하지 못했습니다.'); return; }
  socket.addEventListener('open', () => { setConnection(true); toast('게임 서버에 연결되었습니다.'); send('listrooms'); });
  socket.addEventListener('message', (event) => {
    let data;
    try { data = JSON.parse(event.data); } catch { return; }
    switch (data.type) {
      case 'name_ok':
        nickname = data.nickname || nickname;
        $('nicknameInput').value = nickname;
        $('lobbyNickname').textContent = nickname; $('lobbyAvatar').textContent = nickname.slice(0, 1) || 'ㄱ';
        $('nicknameError').textContent = '';
        showPage('lobby'); send('listrooms'); break;
      case 'room_list':
        roomList = data.rooms || []; renderRooms(); break;
      case 'makeroom_ok':
      case 'room_joined':
      case 'room_update':
        updateRoom(data);
        if (data.type !== 'room_update') showPage('room');
        break;
      case 'game_started':
        gameActive = true;
        $('startGame').disabled = true; $('startGame').innerHTML = '게임 진행 중 <span>⌁</span>';
        showPage('game');
        $('gameLog').replaceChildren();
        $('gameStatus').textContent = data.message || '게임이 시작되었습니다!';
        $('wordInput').disabled = false; $('submitWord').disabled = false;
        addGameLog(data.message || '게임 시작');
        break;
      case 'game_round':
        gameActive = true;
        updateGameRound(data);
        break;
      case 'word_result':
        $('gameStatus').textContent = data.message || '';
        $('wordInput').disabled = false; $('submitWord').disabled = false;
        if (data.ok) addGameLog(data.message || '정답');
        break;
      case 'word_accepted':
        $('gameStatus').textContent = data.message || '정답입니다!';
        $('wordInput').value = '';
        $('wordInput').disabled = true; $('submitWord').disabled = true;
        addGameLog(data.message || '정답');
        renderScores(data.scores || []);
        if (data.fallback_mode) $('gameStatus').textContent += ' · 데모 모드(사전 API 키 미설정)';
        break;
      case 'round_timeout':
        $('gameStatus').textContent = data.message || '시간이 끝났습니다.';
        addGameLog(data.message || '시간 종료');
        $('wordInput').value = '';
        break;
      case 'game_over':
        gameActive = false;
        $('startGame').disabled = !currentIsOwner; $('startGame').innerHTML = '다시 시작 <span>↗</span>';
        stopGameTimer();
        $('gameStatus').textContent = '모든 라운드가 끝났습니다!';
        $('wordInput').disabled = true; $('submitWord').disabled = true;
        renderScores(data.scores || []);
        addGameLog('게임 종료');
        toast('게임이 끝났습니다! 최종 점수를 확인하세요.');
        break;
      case 'room_settings_ok':
        toast(data.message || '방 설정을 변경했습니다.'); break;
      case 'room_left':
        currentRoomId = ''; currentRoomOwner = ''; currentMembers = []; gameActive = false; stopGameTimer();
        showPage('lobby'); send('listrooms'); toast('방에서 나왔습니다.'); break;
      case 'error':
        if (data.code === 'nickname_taken') {
          $('nicknameError').textContent = data.message || '이미 사용 중인 이름입니다. 다른 이름을 입력해주세요.';
          $('nicknameInput').focus();
          toast('이미 사용 중인 이름입니다.');
        } else {
          if (data.code === 'rooms_full' || data.code === 'room_full' || data.code === 'owner_only') toast(data.message || '요청을 처리하지 못했습니다.');
          if (data.code === 'invalid_nickname') $('nicknameError').textContent = data.message || '닉네임을 입력해주세요.';
          if (currentRoomId && currentIsOwner && !gameActive) {
            $('startGame').disabled = false;
            $('startGame').innerHTML = '게임 시작 <span>↗</span>';
          }
          toast(data.message || '요청을 처리하지 못했습니다.');
        }
        break;
      default: break;
    }
  });
  socket.addEventListener('close', () => { setConnection(false); toast('서버 연결이 종료되었습니다. 페이지를 새로고침해 주세요.'); });
  socket.addEventListener('error', () => setConnection(false));
}
function setConnection(connected) {
  $('connectionDot').classList.toggle('connected', connected);
  $('connectionText').textContent = connected ? '서버 연결됨' : '서버 연결 끊김';
}
function updateRoom(data) {
  currentRoomId = data.room_id || currentRoomId;
  currentRoomOwner = data.owner || currentRoomOwner;
  currentIsOwner = typeof data.is_owner === 'boolean' ? data.is_owner : (nickname === currentRoomOwner);
  currentMembers = data.members || currentMembers;
  currentRounds = Number(data.rounds || currentRounds || 10);
  currentMaxPlayers = Number(data.max_players || currentMaxPlayers || 8);
  $('roomRounds').textContent = `${currentRounds}라운드`;
  $('roomRoundsDescription').textContent = `${currentRounds}라운드 · 최대 ${currentMaxPlayers}명`;
  $('roomOwnerSetting').textContent = `방장 ${currentRoomOwner}님이 설정한 게임`;
  $('editRoomSettings').classList.toggle('hidden', !currentIsOwner);
  $('startGame').disabled = !currentIsOwner || data.game_active === true || gameActive;
  $('startGame').innerHTML = data.game_active || gameActive ? '게임 진행 중 <span>⌁</span>' : '게임 시작 <span>↗</span>';
  $('roomCode').textContent = currentRoomId || '------';
  $('memberCount').textContent = String(currentMembers.length);
  const list = $('memberList'); list.replaceChildren();
  currentMembers.forEach((member, index) => {
    const item = document.createElement('div'); item.className = 'member-item';
    const avatar = document.createElement('span'); avatar.className = 'avatar'; avatar.textContent = (member || '?').slice(0, 1);
    const info = document.createElement('div'); const name = document.createElement('div'); name.className = 'member-name'; name.textContent = member;
    info.append(name);
    if (member === currentRoomOwner) { const tag = document.createElement('span'); tag.className = 'owner-tag'; tag.textContent = '★ 방장'; info.append(tag); }
    item.append(avatar, info); list.append(item);
  });
  if (data.type === 'room_update' && currentRoomId && !gameActive) showPage('room');
}

//--------방 목록 렌더링--------
function renderRooms() {
  const list = $('roomList'); list.replaceChildren();
  $('roomTotalCount').textContent = `${roomList.length}/100`;
  $('createRoomButton').disabled = roomList.length >= 100;
  if (roomList.length >= 100) $('createRoomButton').title = '방이 100개로 가득 찼습니다.';
  else $('createRoomButton').removeAttribute('title');
  if (!roomList.length) {
    const empty = document.createElement('div'); empty.className = 'empty-state';
    empty.textContent = '아직 열린 방이 없습니다.\n첫 번째 방을 만들어 보세요.'; list.append(empty); return;
  }
  roomList.forEach((room) => {
    const row = document.createElement('div'); row.className = 'room-row';
    const info = document.createElement('div'); info.className = 'room-info';
    const id = document.createElement('div'); id.className = 'room-id'; id.textContent = room.room_id;
    const meta = document.createElement('div'); meta.className = 'room-meta'; meta.textContent = `방장 ${room.owner} · ${room.members_count}/${room.max_players || 8}명 · ${room.rounds || 10}라운드`;
    info.append(id, meta);
    const button = document.createElement('button'); button.className = 'small-join'; button.type = 'button'; button.textContent = '입장하기';
    if (room.members_count >= (room.max_players || 8)) { button.disabled = true; button.textContent = '인원 초과'; }
    button.addEventListener('click', () => send(`joinroom,${room.room_id}`));
    row.append(info, button); list.append(row);
  });
}

//--------닉네임 입력--------
$('nicknameForm').addEventListener('submit', (event) => {
  event.preventDefault(); const value = $('nicknameInput').value.trim();
  if (!value) { $('nicknameError').textContent = '닉네임을 입력해주세요.'; return; }
  if (value.length > 10) { $('nicknameError').textContent = '닉네임은 10자 이내로 입력해주세요.'; return; }
  if (send(`name,${value}`)) { $('nicknameError').textContent = ''; }
});
$('changeNickname').addEventListener('click', () => { $('nicknameInput').value = nickname; showPage('nickname'); });
//--------방 생성 라운드 설정--------
const createRoomModal = $('createRoomModal');
function openCreateRoomModal() {
  createRoomModal.classList.remove('hidden');
  const selected = document.querySelector('input[name="rounds"]:checked');
  if (selected) selected.closest('.round-option').classList.add('selected');
}
function closeCreateRoomModal() { createRoomModal.classList.add('hidden'); }
function markSelectedOption(input) {
  const fieldset = input.closest('fieldset');
  if (!fieldset) return;
  fieldset.querySelectorAll('.round-option').forEach((option) => option.classList.remove('selected'));
  input.closest('.round-option')?.classList.add('selected');
}
$('createRoomButton').addEventListener('click', openCreateRoomModal);
$('closeCreateRoom').addEventListener('click', closeCreateRoomModal);
$('cancelCreateRoom').addEventListener('click', closeCreateRoomModal);
createRoomModal.addEventListener('click', (event) => {
  if (event.target === createRoomModal) closeCreateRoomModal();
});
document.querySelectorAll('input[type="radio"]').forEach((input) => input.addEventListener('change', () => markSelectedOption(input)));
$('createRoomForm').addEventListener('submit', (event) => {
  event.preventDefault();
  const selected = document.querySelector('input[name="rounds"]:checked');
  const rounds = Number(selected?.value || 10);
  const maxPlayers = Number(document.querySelector('input[name="maxPlayers"]:checked')?.value || 8);
  if (![5, 10, 20].includes(rounds) || ![2, 4, 6, 8, 10].includes(maxPlayers)) { toast('방 설정을 다시 선택해주세요.'); return; }
  if (send(`makeroom,${rounds},${maxPlayers}`)) closeCreateRoomModal();
});
const roomSettingsModal = $('roomSettingsModal');
function openRoomSettings() {
  if (nickname !== currentRoomOwner) { toast('방장만 방 설정을 변경할 수 있습니다.'); return; }
  const roundsInput = document.querySelector(`input[name="editRounds"][value="${currentRounds}"]`);
  const playersInput = document.querySelector(`input[name="editMaxPlayers"][value="${currentMaxPlayers}"]`);
  if (roundsInput) { roundsInput.checked = true; markSelectedOption(roundsInput); }
  if (playersInput) { playersInput.checked = true; markSelectedOption(playersInput); }
  roomSettingsModal.classList.remove('hidden');
}
function closeRoomSettings() { roomSettingsModal.classList.add('hidden'); }
$('editRoomSettings').addEventListener('click', openRoomSettings);
$('closeRoomSettings').addEventListener('click', closeRoomSettings);
$('cancelRoomSettings').addEventListener('click', closeRoomSettings);
roomSettingsModal.addEventListener('click', (event) => { if (event.target === roomSettingsModal) closeRoomSettings(); });
$('roomSettingsForm').addEventListener('submit', (event) => {
  event.preventDefault();
  const rounds = Number(document.querySelector('input[name="editRounds"]:checked')?.value || 10);
  const maxPlayers = Number(document.querySelector('input[name="editMaxPlayers"]:checked')?.value || 8);
  if (![5, 10, 20].includes(rounds) || ![2, 4, 6, 8, 10].includes(maxPlayers)) { toast('방 설정을 다시 선택해주세요.'); return; }
  if (send(`setroomsettings,${rounds},${maxPlayers}`)) closeRoomSettings();
});
$('refreshRooms').addEventListener('click', () => send('listrooms'));
$('joinCodeForm').addEventListener('submit', (event) => {
  event.preventDefault(); const code = $('roomCodeInput').value.trim().toUpperCase();
  if (!/^[A-Z0-9]{6}$/.test(code)) { toast('방 코드는 영문 또는 숫자 6자리입니다.'); return; }
  send(`joinroom,${code}`);
});
$('copyRoomCode').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(currentRoomId); toast('방 코드를 복사했습니다.'); }
  catch { toast(`방 코드: ${currentRoomId}`); }
});
$('backToLobby').addEventListener('click', () => { send('leaveroom'); });
$('leaveRoom').addEventListener('click', () => { send('leaveroom'); });
function addGameLog(message) {
  const log = $('gameLog');
  const empty = log.querySelector('.empty-state'); if (empty) empty.remove();
  const item = document.createElement('div'); item.className = 'game-log-item';
  item.textContent = message; log.prepend(item);
  while (log.children.length > 12) log.lastElementChild.remove();
}
function renderScores(scores) {
  const list = $('scoreList'); list.replaceChildren();
  $('scorePlayerCount').textContent = `${scores.length}명`;
  scores.sort((a, b) => b.score - a.score);
  scores.forEach((entry, index) => {
    const row = document.createElement('div'); row.className = 'score-row';
    const rank = document.createElement('span'); rank.className = 'score-rank'; rank.textContent = String(index + 1).padStart(2, '0');
    const name = document.createElement('span'); name.className = 'score-name'; name.textContent = entry.nickname;
    const score = document.createElement('strong'); score.className = 'score-value'; score.textContent = `${entry.score}점`;
    row.append(rank, name, score); list.append(row);
  });
  if (!scores.length) list.innerHTML = '<div class="empty-state">점수가 여기에 표시됩니다.</div>';
}
function stopGameTimer() { if (gameTimerInterval) clearInterval(gameTimerInterval); gameTimerInterval = null; }
function updateGameRound(data) {
  $('gameRoundEyebrow').textContent = `${data.round}/${data.rounds}`;
  $('promptConsonant').textContent = data.consonant;
  $('promptVowel').textContent = data.vowel;
  $('gameStatus').textContent = `라운드 ${data.round}: 조건에 맞는 단어를 가장 먼저 제출하세요!`;
  $('wordInput').value = ''; $('wordInput').disabled = false; $('submitWord').disabled = false;
  $('wordInput').focus();
  renderScores(data.scores || []);
  gameRoundSeconds = Number(data.seconds || 30); gameEndsAt = Date.now() + gameRoundSeconds * 1000;
  stopGameTimer();
  const tick = () => { const remaining = Math.max(0, Math.ceil((gameEndsAt - Date.now()) / 1000)); $('gameTimer').textContent = String(remaining); if (remaining <= 0) stopGameTimer(); };
  tick(); gameTimerInterval = setInterval(tick, 250);
  addGameLog(`라운드 ${data.round}/${data.rounds} 시작 · ${data.consonant} + ${data.vowel}`);
}
$('wordForm').addEventListener('submit', (event) => {
  event.preventDefault();
  const word = $('wordInput').value.trim();
  if (!word) { $('gameStatus').textContent = '단어를 입력해주세요.'; return; }
  if (send(`submitword,${word}`)) { $('gameStatus').textContent = '단어를 확인하고 있습니다...'; $('submitWord').disabled = true; }
});
$('startGame').addEventListener('click', () => {
  if (!currentIsOwner) { toast('방장만 게임을 시작할 수 있습니다.'); return; }
  if (gameActive) { toast('이미 게임이 진행 중입니다.'); return; }
  if (send('startgame')) { $('startGame').disabled = true; $('startGame').innerHTML = '게임 시작 요청 중...'; }
});
$('exitGame').addEventListener('click', () => { showPage('room'); toast('게임 화면을 나왔습니다. 진행 중인 게임은 계속됩니다.'); });

//--------프로그램 시작--------
connect();
