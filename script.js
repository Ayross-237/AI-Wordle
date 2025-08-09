let state = initialState;

const playerBoardEl = document.getElementById('playerBoard');
const aiBoardEl = document.getElementById('aiBoard');
const newBtn = document.getElementById('newBtn');
const guessBtn = document.getElementById('guessBtn');
const guessInput = document.getElementById('guessInput');
const statusEl = document.getElementById('status');
const aiPanel = document.getElementById('aiPanel');

function buildEmptyBoard() {
  const rows = [];
  for (let r=0;r<6;r++){
    const row = document.createElement('div');
    row.className = 'row';
    for (let c=0;c<5;c++){
      const cell = document.createElement('div');
      cell.className = 'cell';
      cell.textContent = '';
      row.appendChild(cell);
    }
    rows.push(row);
  }
  return rows;
}

let playerRows, aiRows;

function initDOM(){
  playerBoardEl.innerHTML = ''; aiBoardEl.innerHTML = '';
  playerRows = buildEmptyBoard();
  aiRows = buildEmptyBoard();
  playerRows.forEach(r=>playerBoardEl.appendChild(r));
  aiRows.forEach(r=>aiBoardEl.appendChild(r));
  updateFromState();
}

function renderBoardRows(panelRows, boardData, reveal=false) {
  // boardData: list of {guess, feedback}
  // Clear
  panelRows.forEach((row, rIdx) => {
    for (let c=0;c<5;c++){
      const cell = row.children[c];
      cell.className = 'cell';
      cell.textContent = '';
    }
  });

  boardData.forEach((entry, idx) => {
    const g = entry.guess.toUpperCase();
    const fb = entry.feedback;
    const row = panelRows[idx];
    for (let c=0;c<5;c++){
      const cell = row.children[c];
      cell.textContent = g[c];
      cell.classList.add('filled');
      cell.classList.add(fb[c]);
    }
  });

  // If reveal flag true (someone won), remove grayed
  if (reveal) {
    aiPanel.classList.add('revealed');
    aiPanel.classList.remove('grayed');
  } else {
    aiPanel.classList.add('grayed');
    aiPanel.classList.remove('revealed');
  }
}

function updateFromState(){
  // Populate boards
  renderBoardRows(playerRows, state.player.board, state.game_over);
  renderBoardRows(aiRows, state.ai.board, state.game_over);

  // Status string
  if (state.game_over) {
    if (state.player.won && state.ai.won) {
      statusEl.textContent = `Both guessed in ${Math.min(state.player.board.length, state.ai.board.length)} moves!`;
    } else if (state.player.won) {
      statusEl.textContent = `You win! You found "${state.player.target.toUpperCase()}".`;
    } else if (state.ai.won) {
      statusEl.textContent = `AI wins! It found "${state.ai.target.toUpperCase()}".`;
    } else {
      statusEl.textContent = 'Game over.';
    }
    guessBtn.disabled = true;
    guessInput.disabled = true;
  } else {
    statusEl.textContent = `Your attempts: ${state.player.board.length}/6 — AI attempts: ${state.ai.board.length}/6`;
    guessBtn.disabled = false;
    guessInput.disabled = false;
  }
}

async function doNewGame(){
  const res = await fetch('/new', {method:'POST'});
  const j = await res.json();
  state = j.state;
  initDOM();
  guessInput.value = '';
  guessInput.focus();
}

async function submitGuess(){
  const guess = guessInput.value.trim().toLowerCase();
  if (guess.length !== 5) {
    alert("Enter a 5-letter guess.");
    return;
  }
  try {
    const res = await fetch('/guess', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({guess})
    });
    if (!res.ok){
      const err = await res.json();
      alert(err.error || "Invalid guess");
      return;
    }
    const j = await res.json();
    state = j.state;
    updateFromState();
    guessInput.value = '';
    guessInput.focus();
  } catch(e){
    alert("Network error: " + e.message);
  }
}

newBtn.addEventListener('click', doNewGame);
guessBtn.addEventListener('click', submitGuess);
guessInput.addEventListener('keyup', function(e){
  if (e.key === 'Enter') submitGuess();
  // optional: accept only letters
  this.value = this.value.replace(/[^a-zA-Z]/g,'').toUpperCase().slice(0,5);
});

// Initialize visual
initDOM();
