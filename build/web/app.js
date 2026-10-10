//--------WebSocket 연결 설정--------
const WS_PORT = 65535;
const WS_PROTOCOL = location.protocol === 'https:' ? 'wss:' : 'ws:';
const socketUrl = `${WS_PROTOCOL}//${location.hostname}:${WS_PORT}`;
let socket;
let nickname = '';
let currentRoomId = '';
let currentRoomOwner = '';
let currentMembers = [];
let currentRounds = 10;
let roomList = [];
let toastTimer;

//--------화면 요소--------
const $ = (id) => document.getElementById(id);
const pages = { nickname: $('nicknamePage'), lobby: $('lobbyPage'), room: $('roomPage') };
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
        $('lobbyNickname').textContent = nickname; $('lobbyAvatar').textContent = nickname.slice(0, 1) || 'ㄱ';
        showPage('lobby'); send('listrooms'); break;
      case 'room_list':
        roomList = data.rooms || []; renderRooms(); break;
      case 'makeroom_ok':
      case 'room_joined':
      case 'room_update':
        updateRoom(data);
        if (data.type !== 'room_update') showPage('room');
        break;
      case 'room_left':
        currentRoomId = ''; currentRoomOwner = ''; currentMembers = [];
        showPage('lobby'); send('listrooms'); toast('방에서 나왔습니다.'); break;
      case 'error': toast(data.message || '요청을 처리하지 못했습니다.'); break;
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
  currentMembers = data.members || currentMembers;
  currentRounds = Number(data.rounds || currentRounds || 10);
  $('roomRounds').textContent = `${currentRounds}라운드`;
  $('roomRoundsDescription').textContent = `${currentRounds}라운드 · 방장이 설정한 게임 규칙`;
  $('roomOwnerSetting').textContent = `방장 ${currentRoomOwner}님이 설정한 게임`;
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
  if (data.type === 'room_update' && currentRoomId) showPage('room');
}

//--------방 목록 렌더링--------
function renderRooms() {
  const list = $('roomList'); list.replaceChildren();
  if (!roomList.length) {
    const empty = document.createElement('div'); empty.className = 'empty-state';
    empty.textContent = '아직 열린 방이 없습니다.\n첫 번째 방을 만들어 보세요.'; list.append(empty); return;
  }
  roomList.forEach((room) => {
    const row = document.createElement('div'); row.className = 'room-row';
    const info = document.createElement('div'); info.className = 'room-info';
    const id = document.createElement('div'); id.className = 'room-id'; id.textContent = room.room_id;
    const meta = document.createElement('div'); meta.className = 'room-meta'; meta.textContent = `방장 ${room.owner} · ${room.members_count}명 · ${room.rounds || 10}라운드`;
    info.append(id, meta);
    const button = document.createElement('button'); button.className = 'small-join'; button.type = 'button'; button.textContent = '입장하기';
    button.addEventListener('click', () => send(`joinroom,${room.room_id}`));
    row.append(info, button); list.append(row);
  });
}

//--------닉네임 입력--------
$('nicknameForm').addEventListener('submit', (event) => {
  event.preventDefault(); const value = $('nicknameInput').value.trim();
  if (!value) { $('nicknameError').textContent = '닉네임을 입력해주세요.'; return; }
  if (value.length > 10) { $('nicknameError').textContent = '닉네임은 10자 이내로 입력해주세요.'; return; }
  if (send(`name,${value}`)) { nickname = value; $('nicknameError').textContent = ''; }
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
$('createRoomButton').addEventListener('click', openCreateRoomModal);
$('closeCreateRoom').addEventListener('click', closeCreateRoomModal);
$('cancelCreateRoom').addEventListener('click', closeCreateRoomModal);
createRoomModal.addEventListener('click', (event) => {
  if (event.target === createRoomModal) closeCreateRoomModal();
});
document.querySelectorAll('input[name="rounds"]').forEach((input) => {
  input.addEventListener('change', () => {
    document.querySelectorAll('.round-option').forEach((option) => option.classList.remove('selected'));
    input.closest('.round-option').classList.add('selected');
  });
});
$('createRoomForm').addEventListener('submit', (event) => {
  event.preventDefault();
  const selected = document.querySelector('input[name="rounds"]:checked');
  const rounds = Number(selected?.value || 10);
  if (![5, 10, 20].includes(rounds)) { toast('라운드 수를 다시 선택해주세요.'); return; }
  if (send(`makeroom,${rounds}`)) closeCreateRoomModal();
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
$('startGame').addEventListener('click', () => toast('게임 진행 기능은 다음 개발 단계에서 연결할 예정입니다.'));

//--------프로그램 시작--------
connect();
