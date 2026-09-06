// ---------- Global state ----------
let pollInterval = null;
let lastStateString = "";
let personalities = [];
let selectedSeatCount = 4;
let selectedBots = [];      // ordered list of personality keys the player picked
let shownLogCount = 0;      // how many action_log entries we've already rendered
let seatBubbleTimers = {};  // seat -> timeout id, so a fresh taunt cancels the old fade

const SUITS = ['♥', '♦', '♠', '♣'];
const RANKS = { 14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T' };

// Seat layout (percent top/left within the oval table), indexed by seat number.
// Seat 0 (hero) always sits bottom-center; the rest fan out across the top arc.
const SEAT_LAYOUTS = {
  2: [{ t: 90, l: 50 }, { t: 10, l: 50 }],
  3: [{ t: 90, l: 50 }, { t: 22, l: 14 }, { t: 22, l: 86 }],
  4: [{ t: 90, l: 50 }, { t: 46, l: 4 }, { t: 8, l: 50 }, { t: 46, l: 96 }],
  5: [{ t: 90, l: 50 }, { t: 60, l: 6 }, { t: 14, l: 24 }, { t: 14, l: 76 }, { t: 60, l: 94 }],
  6: [{ t: 90, l: 50 }, { t: 66, l: 5 }, { t: 24, l: 10 }, { t: 6, l: 50 }, { t: 24, l: 90 }, { t: 66, l: 95 }],
};

// ---------- Card rendering ----------
function renderCard(cardStr, isBack = false) {
  if (isBack) return `<div class="card-back"></div>`;
  let parsed = cardStr.replace(/[()\s]/g, '').split(',');
  if (parsed.length !== 2) return '';
  let rank = RANKS[parseInt(parsed[0])] || parsed[0];
  let suit = SUITS[parseInt(parsed[1])] || '?';
  let colorClass = (suit === '♥' || suit === '♦') ? 'red' : '';
  return `
    <div class="card ${colorClass}">
      <div class="card-top">${rank}${suit}</div>
      <div class="card-center">${suit}</div>
      <div class="card-bottom" style="transform: rotate(180deg)">${rank}${suit}</div>
    </div>`;
}

// ---------- Setup screen ----------
function renderSeatCountRow() {
  const row = document.getElementById('seat-count-row');
  row.innerHTML = '';
  for (let n = 2; n <= 6; n++) {
    const btn = document.createElement('button');
    btn.className = 'seat-count-btn' + (n === selectedSeatCount ? ' active' : '');
    btn.innerHTML = `${n}<span class="sub">${n === 2 ? 'heads-up' : 'players'}</span>`;
    btn.onclick = () => { selectedSeatCount = n; renderSeatCountRow(); renderRoster(); };
    row.appendChild(btn);
  }
}

function renderRoster() {
  const grid = document.getElementById('roster-grid');
  const needed = selectedSeatCount - 1;
  document.getElementById('pick-counter').innerText = `(${selectedBots.length}/${needed} selected)`;
  grid.innerHTML = '';
  personalities.forEach(p => {
    const isSelected = selectedBots.includes(p.key);
    const card = document.createElement('div');
    card.className = 'roster-card' + (isSelected ? ' selected' : '');
    card.innerHTML = `
      <div class="r-check">&#10003;</div>
      <div class="r-avatar">${p.avatar}</div>
      <div class="r-name">${p.name}</div>
      <div class="r-tag">${p.tagline}</div>
      <span class="r-diff ${p.difficulty}">${p.difficulty}</span>
    `;
    card.onclick = () => {
      const idx = selectedBots.indexOf(p.key);
      if (idx >= 0) {
        selectedBots.splice(idx, 1);
      } else if (selectedBots.length < needed) {
        selectedBots.push(p.key);
      }
      renderRoster();
    };
    grid.appendChild(card);
  });
}

function loadPersonalities() {
  fetch('/api/personalities')
    .then(r => r.json())
    .then(data => {
      personalities = data;
      renderSeatCountRow();
      renderRoster();
    })
    .catch(console.error);
}

function startGame() {
  const needed = selectedSeatCount - 1;
  let bots = selectedBots.slice(0, needed);
  // "Deal Me In" fills any remaining seats randomly from the full roster.
  const pool = personalities.map(p => p.key);
  while (bots.length < needed) {
    const candidate = pool[Math.floor(Math.random() * pool.length)];
    bots.push(candidate);
  }

  document.getElementById('btn-deal-in').disabled = true;
  fetch('/api/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ num_players: selectedSeatCount, bots }),
  })
    .then(r => r.json())
    .then(() => {
      document.getElementById('btn-deal-in').disabled = false;
      document.getElementById('setup-screen').classList.add('hidden');
      document.getElementById('game-screen').classList.remove('hidden');
      document.getElementById('game-over-overlay').classList.add('hidden');
      shownLogCount = 0;
      document.getElementById('log-list').innerHTML = '';
      lastStateString = '';
      if (pollInterval) clearInterval(pollInterval);
      pollInterval = setInterval(pollState, 500);
      pollState();
    })
    .catch(err => {
      document.getElementById('btn-deal-in').disabled = false;
      console.error(err);
    });
}

function resetToSetup() {
  document.getElementById('game-over-overlay').classList.add('hidden');
  document.getElementById('game-screen').classList.add('hidden');
  document.getElementById('setup-screen').classList.remove('hidden');
  selectedBots = [];
  renderRoster();
}

function leaveTable() {
  if (pollInterval) clearInterval(pollInterval);
  fetch('/api/leave', { method: 'POST' }).finally(resetToSetup);
}

// ---------- Polling / rendering ----------
function pollState() {
  fetch('/api/state')
    .then(r => r.json())
    .then(data => updateUI(data))
    .catch(console.error);
}

function money(n) {
  n = n || 0;
  return '$' + n.toFixed(2);
}

function updateUI(state) {
  const currentStateString = JSON.stringify(state);
  if (currentStateString === lastStateString) return;
  lastStateString = currentStateString;

  if (!state.num_players) return; // not started yet / stale poll

  document.getElementById('pot-amount').innerText = money(state.pot);
  document.getElementById('board-cards').innerHTML = (state.board || []).map(c => renderCard(c)).join('');
  document.getElementById('hand-meta').innerText =
    `Hand ${state.hand_number || 1} · ${['Preflop', 'Flop', 'Turn', 'River', 'Showdown'][state.street] || ''}`;

  const players = state.players || [];
  const hero = players.find(p => p.is_hero);
  document.getElementById('hero-stack').innerText = money(hero ? hero.stack : (state.stacks ? state.stacks[0] : 0));
  document.getElementById('hero-cards').innerHTML = (state.hero_cards || []).map(c => renderCard(c)).join('');

  renderSeats(state);
  renderLog(state);
  renderDecisionLog(state);

  // Action panel
  const actionPanel = document.getElementById('action-panel');
  const waitingNote = document.getElementById('waiting-note');
  const resultBanner = document.getElementById('result-banner');

  if (state.waiting_for_human) {
    resultBanner.classList.add('hidden');
    waitingNote.classList.add('hidden');
    let html = '';
    (state.legal_actions || []).forEach(act => {
      const cls = act === 'FOLD' ? 'btn-fold' : (act.startsWith('BET') || act === 'ALL_IN' ? 'btn-bet' : 'btn-check-call');
      html += `<button class="action-btn ${cls}" onclick="sendAction('${act}')">${act.replace('_', ' ')}</button>`;
    });
    actionPanel.innerHTML = html;
  } else {
    actionPanel.innerHTML = '';
    if (!state.hand_over) {
      waitingNote.classList.remove('hidden');
    } else {
      waitingNote.classList.add('hidden');
    }
  }

  if (state.hand_over && !state.waiting_for_human && state.last_result) {
    const res = state.last_result;
    resultBanner.classList.remove('hidden');
    const heroIdx = 0;
    const heroDelta = res.chip_delta ? res.chip_delta[heroIdx] : 0;
    let title;
    if (res.outcome === 'fold') title = res.winner_names.includes('You') ? 'Everyone folded — you win the pot' : `${res.winner_names.join(' & ')} takes it`;
    else if (res.winner_names.includes('You')) title = 'You win the showdown!';
    else if (heroDelta === 0) title = 'Split pot';
    else title = `${res.winner_names.join(' & ')} wins the showdown`;
    document.getElementById('result-title').innerText = title;
    document.getElementById('result-sub').innerText =
      `${heroDelta >= 0 ? '+' : ''}${heroDelta.toFixed(2)} chips for you this hand.`;
  }

  if (state.game_over) {
    if (pollInterval) clearInterval(pollInterval);
    const overlay = document.getElementById('game-over-overlay');
    overlay.classList.remove('hidden');
    const reason = state.game_over_reason;
    const emoji = document.getElementById('go-emoji');
    const title = document.getElementById('go-title');
    const sub = document.getElementById('go-sub');
    if (reason === 'human_busted') {
      emoji.innerHTML = '&#128128;';
      title.innerText = 'Busted';
      sub.innerText = "You're out of chips. The table plays on without you — want a rematch?";
    } else if (reason === 'human_wins') {
      emoji.innerHTML = '&#127942;';
      title.innerText = 'Table Cleared!';
      sub.innerText = 'Every bot busted. You own this table.';
    } else {
      emoji.innerHTML = '&#128075;';
      title.innerText = 'Table Closed';
      sub.innerText = 'Come back any time.';
    }
  }
}

function renderSeats(state) {
  const container = document.getElementById('seats-container');
  const layout = SEAT_LAYOUTS[state.num_players] || SEAT_LAYOUTS[4];
  const players = state.players && state.players.length ? state.players : (state.seat_meta || []).map((m, i) => ({
    seat: i, is_hero: i === 0, key: m.key, name: m.name, avatar: m.avatar,
    stack: (state.stacks && state.stacks[i]) || 0, street_bet: 0, folded: false, all_in: false,
  }));
  if (!players.length) return;

  container.innerHTML = '';
  players.forEach((p, i) => {
    const pos = layout[i] || layout[layout.length - 1];
    const seatEl = document.createElement('div');
    seatEl.className = 'seat' + (p.is_hero ? ' is-hero' : '') + (p.folded ? ' folded' : '');
    seatEl.style.top = pos.t + '%';
    seatEl.style.left = pos.l + '%';

    const isActing = !state.hand_over && state.current_seat === p.seat;
    if (isActing) seatEl.classList.add('acting');

    const isDealer = state.button === p.seat;
    const cardsHtml = p.is_hero ? '' : `<div class="seat-cards">${p.folded ? '' : renderCard('', true) + renderCard('', true)}</div>`;
    const roleBadge = p.is_sb ? '<div class="seat-role-btn seat-role-sb">SB</div>'
      : p.is_bb ? '<div class="seat-role-btn seat-role-bb">BB</div>' : '';

    seatEl.innerHTML = `
      <div class="seat-avatar-wrap">
        <div class="seat-avatar">${p.avatar || '🤖'}</div>
        ${isDealer ? '<div class="seat-dealer-btn">D</div>' : roleBadge}
      </div>
      <div class="seat-name">${p.name}</div>
      <div class="seat-stack">${money(p.stack)}</div>
      ${p.street_bet ? `<div class="seat-bet-chip"><span class="dot"></span>${money(p.street_bet)}</div>` : ''}
      ${cardsHtml}
      ${p.all_in ? '<div class="seat-badge-allin">ALL IN</div>' : ''}
    `;
    container.appendChild(seatEl);
  });

  // Reveal cards at showdown, if we have a result for this poll
  if (state.hand_over && state.last_result && state.last_result.reveals) {
    Object.entries(state.last_result.reveals).forEach(([seatStr, cards]) => {
      const seat = parseInt(seatStr);
      if (seat === 0) return; // hero's own cards already shown
      const seatEls = container.children;
      const el = seatEls[seat];
      if (el) {
        const cardsDiv = el.querySelector('.seat-cards');
        if (cardsDiv) cardsDiv.innerHTML = cards.map(c => renderCard(c)).join('');
      }
    });
  }
}

function renderLog(state) {
  const log = state.action_log || [];
  const list = document.getElementById('log-list');
  const newEntries = log.slice(shownLogCount);
  newEntries.forEach(e => {
    const div = document.createElement('div');
    div.className = 'log-entry';
    const tagClass = (e.trigger || '').toLowerCase();
    const actionLabel = e.action ? e.action.replace('_', ' ') : (e.trigger === 'win' ? 'WINS' : e.trigger === 'lose' ? 'LOSES' : '');
    div.innerHTML = `
      <div class="le-avatar">${e.avatar}</div>
      <div class="le-body">
        <b>${e.name}</b> <span class="le-action-tag ${tagClass}">${actionLabel}</span>
        ${e.taunt ? `<span class="le-taunt">&ldquo;${e.taunt}&rdquo;</span>` : ''}
      </div>`;
    list.insertBefore(div, list.firstChild);

    // Also float it as a speech bubble over the seat, if we can find it.
    if (e.taunt) showBubble(e.seat, e.taunt, state.num_players);
  });
  shownLogCount = log.length;
  // Cap the DOM list so a long session doesn't bloat the page.
  while (list.children.length > 80) list.removeChild(list.lastChild);
}

function showBubble(seat, text, numPlayers) {
  const container = document.getElementById('seats-container');
  if (!container || !container.children[seat]) return;
  const seatEl = container.children[seat];
  const old = seatEl.querySelector('.speech-bubble');
  if (old) old.remove();
  const bubble = document.createElement('div');
  // Seats sitting near the top of the oval table don't have room for a
  // bubble rendered above them -- flip it below for those seats instead.
  const layout = SEAT_LAYOUTS[numPlayers] || SEAT_LAYOUTS[4];
  const pos = layout[seat] || layout[layout.length - 1];
  const nearTop = pos && pos.t <= 25;
  bubble.className = 'speech-bubble' + (nearTop ? ' speech-bubble-below' : '');
  bubble.innerText = text;
  seatEl.appendChild(bubble);
  clearTimeout(seatBubbleTimers[seat]);
  seatBubbleTimers[seat] = setTimeout(() => bubble.remove(), 3600);
}

// ---------- Post-hand decision rationale ("why did they play that way") ----------
// Revealed only once a hand is over (state.last_result.decision_log is only ever
// populated server-side after the hand ends -- see app.py's hand_ctx), so this
// never leaks a bot's hand strength while the hand is still live.
function togglePanel(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('hidden');
}

function renderDecisionLog(state) {
  const log = (state.last_result && state.last_result.decision_log) || [];
  const html = log.length
    ? log.map(e => `
        <div class="rationale-entry">
          <div class="ra-head">
            <span class="ra-avatar">${e.avatar || ''}</span>
            <b>${e.name || ('Seat ' + e.seat)}</b>
            <span class="ra-action">${(e.action || '').replace('_', ' ')}</span>
          </div>
          <div class="ra-summary">${e.summary || ''}</div>
        </div>`).join('')
    : '<div class="rationale-empty">Nothing to explain yet.</div>';
  ['rationale-panel', 'go-rationale-panel'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  });
}

function sendAction(action) {
  document.getElementById('action-panel').innerHTML = '';
  fetch('/api/action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  }).then(() => pollState());
}

function requestNextHand() {
  document.getElementById('result-banner').classList.add('hidden');
  fetch('/api/next_hand', { method: 'POST' }).then(() => pollState());
}

// ---------- Boot ----------
loadPersonalities();
