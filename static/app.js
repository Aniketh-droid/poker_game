// ---------- Global state ----------
let pollInterval = null;
let lastStateString = "";
let personalities = [];
let selectedSeatCount = 4;
let selectedBots = [];      // ordered list of personality keys the player picked
let shownBubbleCount = 0;   // how many action_log entries we've floated as taunts
let seatBubbleTimers = {};  // seat -> timeout id, so a fresh taunt cancels the old fade
let lastBoardSig = '';      // last board rendered, to skip redundant re-renders
let lastHeroSig = '';       // last hero hole cards rendered
let seatCache = {};         // seat index -> { el, sig, cls, pos } for in-place updates
let ledgerHand = 0;         // hand number The Play column is currently showing
let entryHand = [];         // action_log index -> hand number it was observed under
let taggedLen = 0;          // how much of action_log we've tagged
let playPinned = null;      // index of the pinned move in The Play, or null
let sessionLog = [];        // one entry per settled hand: { hand, outcome, delta }
let lastRecordedHand = 0;   // highest hand number already pushed into sessionLog

const SUITS = ['♥', '♦', '♠', '♣'];
const SUIT_NAMES = { '♥': 'hearts', '♦': 'diamonds', '♠': 'spades', '♣': 'clubs' };
const RANKS = { 14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T' };
const RANK_NAMES = { A: 'ace', K: 'king', Q: 'queen', J: 'jack', T: 'ten' };
const STREET_NAMES = ['Preflop', 'Flop', 'Turn', 'River', 'Showdown'];
const STREET_STEPS = ['Pre', 'Flop', 'Turn', 'River'];
// Triggers worth weighting heavier in the Table Talk column.
const LOUD_TRIGGERS = new Set(['win', 'lose', 'bad_beat', 'bluff_win']);

// The model behind each personality, stated plainly. Every line is a real,
// documented fact about that agent (see agents/*.py and the README roster) --
// this is the "claim" (tagline) paired with its "proof".
const MODEL_FACT = {
  'wildcard': 'Uniformly random legal action. No hand reading, no plan — the baseline.',
  'calling-station': 'Static loose-passive rules. ~3% fold rate, almost never raises.',
  'the-rock': 'Deterministic hand-bucket rules. Folds all but premium holdings; no simulation.',
  'the-mathematician': 'Monte-Carlo expected value, ~70 sims per decision. Assumes your range is random.',
  'the-maniac': 'Static loose-aggressive rules. Fires a bet or raise ~75% of the time, near hand-independent.',
  'the-profiler': 'Bayesian belief over your hand bucket, tracked per seat. Adapts to your observed fold/call rate.',
  'the-data-scientist': 'Ensemble: averages a Monte-Carlo EV model and the Bayesian belief model 50/50.',
};

// Seat layout (percent top/left within the oval table), indexed by seat number.
// Seat 0 (hero) always sits bottom-center; the rest fan out across the top arc.
const SEAT_LAYOUTS = {
  2: [{ t: 89, l: 50 }, { t: 13, l: 50 }],
  3: [{ t: 89, l: 50 }, { t: 20, l: 22 }, { t: 20, l: 78 }],
  4: [{ t: 89, l: 50 }, { t: 50, l: 12 }, { t: 13, l: 50 }, { t: 50, l: 88 }],
  5: [{ t: 89, l: 50 }, { t: 60, l: 13 }, { t: 19, l: 26 }, { t: 19, l: 74 }, { t: 60, l: 87 }],
  6: [{ t: 89, l: 50 }, { t: 64, l: 13 }, { t: 28, l: 16 }, { t: 13, l: 50 }, { t: 28, l: 84 }, { t: 64, l: 87 }],
};

// On a narrow portrait plate the seats need to hug the rim harder so their
// labels don't crowd the pot.
const MOBILE_SEAT_LAYOUTS = {
  2: [{ t: 91, l: 50 }, { t: 10, l: 50 }],
  3: [{ t: 91, l: 50 }, { t: 15, l: 17 }, { t: 15, l: 83 }],
  4: [{ t: 91, l: 50 }, { t: 45, l: 7 }, { t: 10, l: 50 }, { t: 45, l: 93 }],
  5: [{ t: 91, l: 50 }, { t: 56, l: 8 }, { t: 13, l: 22 }, { t: 13, l: 78 }, { t: 56, l: 92 }],
  6: [{ t: 91, l: 50 }, { t: 60, l: 8 }, { t: 24, l: 11 }, { t: 10, l: 50 }, { t: 24, l: 89 }, { t: 60, l: 92 }],
};
function layoutFor(n) {
  return ((window.innerWidth <= 620 ? MOBILE_SEAT_LAYOUTS : SEAT_LAYOUTS)[n]) || SEAT_LAYOUTS[4];
}

// ---------- Helpers ----------
function mark(key) {
  return (window.BnB && window.BnB.botMark) ? window.BnB.botMark(key) : '';
}

function seatKey(state, seat) {
  const meta = (state.seat_meta || [])[seat];
  return meta ? meta.key : null;
}

// ---------- Card rendering ----------
function renderCard(cardStr, isBack = false) {
  if (isBack) return `<div class="card-back" aria-hidden="true"></div>`;
  let parsed = cardStr.replace(/[()\s]/g, '').split(',');
  if (parsed.length !== 2) return '';
  let rank = RANKS[parseInt(parsed[0])] || parsed[0];
  let suit = SUITS[parseInt(parsed[1])] || '?';
  let colorClass = (suit === '♥' || suit === '♦') ? 'red' : '';
  let label = `${RANK_NAMES[rank] || rank} of ${SUIT_NAMES[suit] || ''}`.trim();
  return `
    <div class="card ${colorClass}" role="img" aria-label="${label}">
      <div class="card-top" aria-hidden="true">${rank}${suit}</div>
      <div class="card-center" aria-hidden="true">${suit}</div>
      <div class="card-bottom" aria-hidden="true" style="transform: rotate(180deg)">${rank}${suit}</div>
    </div>`;
}

// ---------- Setup screen ----------
function renderSeatCountRow() {
  const row = document.getElementById('seat-count-row');
  row.innerHTML = '';
  for (let n = 2; n <= 6; n++) {
    const btn = document.createElement('button');
    btn.className = 'seat-count-btn' + (n === selectedSeatCount ? ' active' : '');
    btn.setAttribute('aria-pressed', n === selectedSeatCount ? 'true' : 'false');
    btn.innerHTML = `${n}<span class="sub">${n === 2 ? 'heads-up' : 'seats'}</span>`;
    btn.onclick = () => { selectedSeatCount = n; renderSeatCountRow(); renderRoster(); };
    row.appendChild(btn);
  }
}

function renderRoster() {
  const grid = document.getElementById('roster-grid');
  const needed = selectedSeatCount - 1;
  document.getElementById('pick-counter').innerText = `${selectedBots.length} of ${needed} chosen`;
  grid.innerHTML = '';
  personalities.forEach(p => {
    const isSelected = selectedBots.includes(p.key);
    const card = document.createElement('div');
    card.className = 'roster-card' + (isSelected ? ' selected' : '');
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');
    card.setAttribute('aria-pressed', isSelected ? 'true' : 'false');
    card.setAttribute('aria-label', `${p.name}. ${p.tagline} ${MODEL_FACT[p.key] || ''}`);
    card.innerHTML = `
      <div class="r-avatar" aria-hidden="true">${mark(p.key)}</div>
      <div class="r-name">${p.name}</div>
      <div class="r-tag">${p.tagline}</div>
      <div class="r-model">${MODEL_FACT[p.key] || ''}</div>
      <span class="r-diff ${p.difficulty}">${p.difficulty}</span>
      <div class="r-check" aria-hidden="true">${(window.BnB && window.BnB.tick) ? window.BnB.tick() : ''}</div>
    `;
    const toggle = () => {
      const idx = selectedBots.indexOf(p.key);
      if (idx >= 0) selectedBots.splice(idx, 1);
      else if (selectedBots.length < needed) selectedBots.push(p.key);
      renderRoster();
    };
    card.onclick = toggle;
    card.onkeydown = (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
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
      shownBubbleCount = 0;
      ledgerHand = 0; entryHand = []; taggedLen = 0; playPinned = null;
      sessionLog = []; lastRecordedHand = 0;
      document.getElementById('session-list').innerHTML = '';
      document.getElementById('rr-balance').innerHTML = '';
      document.getElementById('standings-list').innerHTML = '';
      seatCache = {}; lastBoardSig = ''; lastHeroSig = '';
      document.getElementById('seats-container').innerHTML = '';
      document.getElementById('log-list').innerHTML = '';
      document.getElementById('play-detail').innerHTML = '';
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

// The running account in the ledger header — stack, session P/L, hand & street.
function renderLedgerHead(state, hero) {
  const stackEl = document.getElementById('lh-stack');
  const sessEl = document.getElementById('lh-session');
  const metaEl = document.getElementById('hand-meta');
  const track = document.getElementById('street-track');
  if (!stackEl) return;

  const stack = hero ? hero.stack : (state.stacks ? state.stacks[0] : 0);
  stackEl.innerText = money(stack);
  const delta = stack - 50; // STARTING_STACK is 50 * BB(=1)
  sessEl.innerText = (delta >= 0 ? '+' : '−') + '$' + Math.abs(delta).toFixed(2);
  const fig = sessEl.closest('.lh-fig');
  if (fig) {
    fig.classList.toggle('is-up', delta > 0.001);
    fig.classList.toggle('is-down', delta < -0.001);
  }

  metaEl.innerText = `Hand ${state.hand_number || 1} · ${STREET_NAMES[state.street] || ''}`;
  const s = state.street || 0;
  const tk = (window.BnB && window.BnB.tick) ? window.BnB.tick() : '';
  track.innerHTML = STREET_STEPS.map((label, i) => {
    const done = (s >= 4 || i < s);
    const cls = 'st-step' + (done ? ' done' : (i === s ? ' now' : ''));
    return `<span class="${cls}">${done ? tk : ''}${label}</span>`;
  }).join('');
}

// ---------- The room rail — standings + running session account ----------
function renderRoomRail(state) {
  const meta = document.getElementById('rr-meta');
  if (!meta) return;
  meta.textContent = `${state.num_players} seats · $0.50 / $1.00`;
  renderStandings(state);
  renderSession(state);
}

function renderStandings(state) {
  const el = document.getElementById('standings-list');
  if (!el) return;
  const players = (state.players && state.players.length) ? state.players.slice() : [];
  if (!players.length) { el.innerHTML = ''; return; }
  const max = Math.max(1, ...players.map(p => p.stack || 0));
  const ranked = players.sort((a, b) => (b.stack || 0) - (a.stack || 0));
  el.innerHTML = ranked.map(p => {
    const key = p.key || seatKey(state, p.seat);
    const out = (p.stack || 0) < 0.005;
    const pct = out ? 0 : Math.max(3, Math.round(((p.stack || 0) / max) * 100));
    const cls = 'rr-seat' + (p.is_hero ? ' is-hero' : '') + (p.folded ? ' is-folded' : '') + (out ? ' is-out' : '');
    return `<div class="${cls}">
        <span class="rr-mark" aria-hidden="true">${mark(key)}</span>
        <span class="rr-name">${p.name}</span>
        <span class="rr-stack">${out ? 'out' : money(p.stack)}</span>
      </div>
      <div class="rr-bar"><span style="width:${pct}%"></span></div>`;
  }).join('');
}

function renderSession(state) {
  const list = document.getElementById('session-list');
  const bal = document.getElementById('rr-balance');
  if (!list || !bal) return;

  if (!sessionLog.length) {
    list.innerHTML = `<div class="rr-empty">No hands settled yet — each one is written in here as it finishes.</div>`;
    bal.className = 'rr-balance';
    bal.innerHTML = '';
    return;
  }

  list.innerHTML = sessionLog.map(h => {
    const up = h.delta > 0.001, down = h.delta < -0.001;
    const cls = 'rr-hand' + (up ? ' is-up' : (down ? ' is-down' : ''));
    const amt = (h.delta >= 0 ? '+' : '−') + '$' + Math.abs(h.delta).toFixed(2);
    return `<div class="${cls}"><span class="rr-h-label">Hand ${h.hand}</span><span class="rr-h-note">${amt}</span></div>`;
  }).join('');
  list.scrollTop = list.scrollHeight;

  const hero = (state.players || []).find(p => p.is_hero);
  const net = hero ? (hero.stack - 50) : sessionLog.reduce((s, h) => s + h.delta, 0);
  const up = net > 0.001, down = net < -0.001;
  bal.className = 'rr-balance' + (up ? ' is-up' : (down ? ' is-down' : ''));
  bal.innerHTML = `<span>Net</span><b>${(net >= 0 ? '+' : '−')}$${Math.abs(net).toFixed(2)}</b>`;
}

function updateUI(state) {
  const currentStateString = JSON.stringify(state);
  if (currentStateString === lastStateString) return;
  lastStateString = currentStateString;

  if (!state.num_players) return; // not started yet / stale poll

  document.getElementById('pot-amount').innerText = money(state.pot);

  // Only touch the board / hero cards when they actually change — re-setting
  // identical innerHTML every poll re-fires the deal animation and jitters.
  const boardSig = (state.board || []).join(',');
  if (boardSig !== lastBoardSig) {
    document.getElementById('board-cards').innerHTML = (state.board || []).map(c => renderCard(c)).join('');
    lastBoardSig = boardSig;
  }

  const players = state.players || [];
  const hero = players.find(p => p.is_hero);
  document.getElementById('hero-stack').innerText = money(hero ? hero.stack : (state.stacks ? state.stacks[0] : 0));
  const heroSig = (state.hero_cards || []).join(',');
  if (heroSig !== lastHeroSig) {
    document.getElementById('hero-cards').innerHTML = (state.hero_cards || []).map(c => renderCard(c)).join('');
    lastHeroSig = heroSig;
  }
  renderLedgerHead(state, hero);

  // The running session account — record each hand once it settles.
  if (state.hand_over && state.last_result) {
    const rh = state.last_result.hand_number;
    if (rh && rh > lastRecordedHand) {
      lastRecordedHand = rh;
      sessionLog.push({
        hand: rh,
        outcome: state.last_result.outcome,
        delta: (state.last_result.chip_delta || [])[0] || 0,
      });
    }
  }

  renderSeats(state);
  renderPlayLedger(state);
  renderRoomRail(state);
  renderBubbles(state);

  // Post-hand the leather action rail has nothing to do — step it aside so the
  // result leaf and the next deal aren't stacked against a dead panel.
  const heroPanel = document.getElementById('hero-panel');
  heroPanel.classList.toggle('hidden', !!(state.hand_over && !state.waiting_for_human));

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
    if (res.outcome === 'fold') title = res.winner_names.includes('You') ? 'Everyone folded — the pot is yours' : `${res.winner_names.join(' & ')} takes it`;
    else if (res.winner_names.includes('You')) title = 'You win the showdown';
    else if (heroDelta === 0) title = 'Split pot';
    else title = `${res.winner_names.join(' & ')} wins the showdown`;
    document.getElementById('result-title').innerText = title;
    document.getElementById('result-sub').innerText =
      `${heroDelta >= 0 ? '+' : ''}${heroDelta.toFixed(2)} to your account this hand · hover a move in The Play to see the read behind it.`;
    const rc = document.getElementById('result-cards');
    const hc = (state.hero_cards && state.hero_cards.length)
      ? state.hero_cards
      : ((res.reveals && res.reveals['0']) || []);
    rc.innerHTML = hc.map(c => renderCard(c)).join('');
  }

  if (state.game_over) {
    if (pollInterval) clearInterval(pollInterval);
    const overlay = document.getElementById('game-over-overlay');
    overlay.classList.remove('hidden');
    const reason = state.game_over_reason;
    const emoji = document.getElementById('go-emoji');
    const title = document.getElementById('go-title');
    const sub = document.getElementById('go-sub');
    emoji.innerHTML = (window.BnB && window.BnB.outcomeMark) ? window.BnB.outcomeMark(reason) : '';
    if (reason === 'human_busted') {
      title.innerText = 'Busted';
      sub.innerText = "You're out of chips. The table plays on without you — want a rematch?";
    } else if (reason === 'human_wins') {
      title.innerText = 'Table Cleared';
      sub.innerText = 'Every bot busted. You own this room.';
    } else {
      title.innerText = 'Table Closed';
      sub.innerText = 'Come back any time.';
    }
  }
}

// Cumulative fold/aggression read per seat, from this match's action log only.
// Same idea The Profiler tracks server-side; here it's just the visible history.
function computeTendencies(state) {
  const out = {};
  (state.action_log || []).forEach(e => {
    if (!e.action) return;
    const t = e.trigger;
    if (!['fold', 'check', 'call', 'bet', 'raise'].includes(t)) return;
    const s = out[e.seat] || (out[e.seat] = { fold: 0, aggr: 0, n: 0 });
    s.n += 1;
    if (t === 'fold') s.fold += 1;
    if (t === 'bet' || t === 'raise') s.aggr += 1;
  });
  return out;
}

// The seat gauge only shows once a bot has revealed an actual tell — a clear
// lean toward folding, betting, or calling. No "reading…" or "mixed" clutter.
function tendencyMarkup(td) {
  const n = td ? td.n : 0;
  if (n < 10) return '';
  const agg = td.aggr / n;
  const foldPct = Math.round((td.fold / n) * 100);
  let word = '';
  if (foldPct >= 45) word = 'folds often';
  else if (agg >= 0.45) word = 'bets often';
  else if (agg <= 0.1 && foldPct < 15) word = 'calls often';
  if (!word) return '';
  const lean = (td.aggr - td.fold) / n;
  const pos = Math.round((lean + 1) * 50);
  const title = `This match, observed: ${td.aggr} bets/raises, folded ${foldPct}%, across ${n} decisions`;
  return `<div class="seat-tendency" title="${title}">
    <div class="td-track" aria-hidden="true"><span class="td-mark" style="left:${pos}%"></span></div>
    <div class="td-label">${word}</div>
  </div>`;
}

// ---------- Seats (updated in place; a full rebuild each poll jitters) ----------
function seatInner(p, key, state, tendencies) {
  const isDealer = state.button === p.seat;
  const roleBadge = p.is_sb ? '<div class="seat-role-btn seat-role-sb" title="Small blind">SB</div>'
    : p.is_bb ? '<div class="seat-role-btn seat-role-bb" title="Big blind">BB</div>' : '';
  const badge = isDealer ? '<div class="seat-dealer-btn" title="Dealer button">D</div>' : roleBadge;
  const cardsHtml = p.is_hero ? '' : `<div class="seat-cards">${p.folded ? '' : renderCard('', true) + renderCard('', true)}</div>`;
  return `
    <div class="seat-avatar-wrap">
      <div class="seat-avatar" aria-hidden="true">${mark(key)}</div>
      ${badge}
    </div>
    <div class="seat-name">${p.name}</div>
    <div class="seat-stack">${money(p.stack)}</div>
    ${p.is_hero ? '' : tendencyMarkup(tendencies[p.seat])}
    ${p.street_bet ? `<div class="seat-bet-chip"><span class="dot" aria-hidden="true"></span>${money(p.street_bet)}</div>` : ''}
    ${cardsHtml}
    ${p.all_in ? '<div class="seat-badge-allin">All in</div>' : ''}
  `;
}

function renderSeats(state) {
  const container = document.getElementById('seats-container');
  const layout = layoutFor(state.num_players);
  const players = state.players && state.players.length ? state.players : (state.seat_meta || []).map((m, i) => ({
    seat: i, is_hero: i === 0, key: m.key, name: m.name, avatar: m.avatar,
    stack: (state.stacks && state.stacks[i]) || 0, street_bet: 0, folded: false, all_in: false,
  }));
  if (!players.length) return;
  const tendencies = computeTendencies(state);

  if (container.childElementCount !== players.length) {
    container.innerHTML = '';
    seatCache = {};
    players.forEach((_, i) => {
      const el = document.createElement('div');
      container.appendChild(el);
      seatCache[i] = { el, sig: null, cls: null, pos: null };
    });
  }

  players.forEach((p, i) => {
    const c = seatCache[i];
    if (!c) return;
    const pos = layout[i] || layout[layout.length - 1];
    const key = p.key || seatKey(state, p.seat);
    const isActing = !state.hand_over && state.current_seat === p.seat;

    const cls = 'seat' + (p.is_hero ? ' is-hero' : '') + (p.folded ? ' folded' : '')
      + (pos.t < 16 && Math.abs(pos.l - 50) < 12 ? ' seat-top' : '')
      + (isActing ? ' acting' : '');
    if (cls !== c.cls) { c.el.className = cls; c.cls = cls; }

    const posStr = pos.t + '|' + pos.l;
    if (posStr !== c.pos) {
      c.el.style.top = pos.t + '%';
      c.el.style.left = pos.l + '%';
      c.pos = posStr;
    }

    const td = tendencies[p.seat];
    const sig = [
      p.name, key, Math.round(p.stack * 100), p.folded, p.all_in,
      Math.round((p.street_bet || 0) * 100), state.button === p.seat, p.is_sb, p.is_bb,
      td ? td.n : 0,
    ].join('|');
    if (sig !== c.sig) {
      c.el.innerHTML = seatInner(p, key, state, tendencies);
      c.sig = sig;
    }
  });

  // Reveal cards at showdown — touch only the one .seat-cards, once.
  if (state.hand_over && state.last_result && state.last_result.reveals) {
    Object.entries(state.last_result.reveals).forEach(([seatStr, cards]) => {
      const seat = parseInt(seatStr);
      if (seat === 0) return;
      const c = seatCache[seat];
      if (!c) return;
      const cd = c.el.querySelector('.seat-cards');
      if (cd && cd.dataset.revealed !== '1') {
        cd.innerHTML = cards.map(x => renderCard(x)).join('');
        cd.dataset.revealed = '1';
      }
    });
  }
}

// ---------- The Play — this hand's moves, each opening its own read ----------
const ACT_WORD = {
  FOLD: 'folds', CHECK: 'checks', CALL: 'calls',
  BET_25: 'bets ¼ pot', BET_50: 'bets ½ pot', BET_100: 'bets the pot',
  ALL_IN: 'all in',
};
function moveWord(e) {
  if (e.trigger === 'raise' && e.action && e.action.indexOf('BET') === 0) {
    return e.action === 'BET_100' ? 'raises pot' : e.action === 'BET_50' ? 'raises ½ pot' : 'raises ¼ pot';
  }
  return ACT_WORD[e.action] || String(e.action || '').replace('_', ' ').toLowerCase();
}
function playDefaultDetail(handOver) {
  return `<div class="pd-empty">${handOver
    ? 'Hover or tap a move to see the read behind it.'
    : 'Each read opens once the hand is done.'}</div>`;
}

let playRows = [];

function renderPlayLedger(state) {
  const list = document.getElementById('log-list');
  const detail = document.getElementById('play-detail');
  const log = state.action_log || [];

  // Tag every new log entry with the hand it was seen under — a robust way to
  // slice out "this hand's moves" without racing the action stream.
  if (log.length < taggedLen) { entryHand = []; taggedLen = 0; }
  for (let i = taggedLen; i < log.length; i++) entryHand[i] = state.hand_number;
  taggedLen = log.length;

  const hn = state.hand_number || 1;
  if (hn !== ledgerHand) { ledgerHand = hn; playPinned = null; }

  const moves = log.filter((e, i) => e.action && entryHand[i] === hn);
  const decisions = (state.last_result && state.last_result.decision_log) || [];
  let di = 0;
  playRows = moves.map((m) => {
    let dec = null;
    if (m.seat !== 0) { dec = decisions[di] || null; di++; }
    return { m, dec };
  });

  const byStreet = [[], [], [], [], []];
  playRows.forEach((r, idx) => { (byStreet[r.m.street] || byStreet[0]).push({ r, idx }); });

  let html = '';
  STREET_NAMES.forEach((sn, s) => {
    if (s > 3 || !byStreet[s].length) return;
    html += `<div class="pl-street">${sn}</div>`;
    byStreet[s].forEach(({ r, idx }) => {
      const key = seatKey(state, r.m.seat);
      const live = !!r.dec;
      const tag = live ? 'button' : 'div';
      html += `<${tag} class="pl-move${r.m.seat === 0 ? ' is-hero' : ''}${live ? ' has-read' : ''}${playPinned === idx ? ' pinned' : ''}"${live ? ` type="button" data-move="${idx}"` : ''}>
        <span class="pl-who"><span class="pl-mark" aria-hidden="true">${mark(key)}</span>${r.m.name}</span>
        <span class="pl-act">${moveWord(r.m)}</span>
      </${tag}>`;
    });
  });
  if (!playRows.length) html = `<div class="pl-empty">The hand hasn’t been dealt.</div>`;
  list.innerHTML = html;

  if (!state.hand_over) list.scrollTop = list.scrollHeight;

  if (playPinned != null && playRows[playPinned] && playRows[playPinned].dec) {
    showPlayDetail(playPinned, true);
  } else {
    detail.innerHTML = playDefaultDetail(state.hand_over);
  }
}

function showPlayDetail(idx, pinned) {
  const r = playRows[idx];
  const detail = document.getElementById('play-detail');
  if (!r || !r.dec) return;
  detail.innerHTML = `
    <div class="pd-head">${r.m.name}<span class="pd-act">${moveWord(r.m)}</span></div>
    <div class="pd-street">${STREET_NAMES[r.m.street] || ''} · the read</div>
    <div class="pd-body">${r.dec.summary || 'No read recorded for this move.'}</div>`;
  detail.classList.toggle('is-pinned', !!pinned);
}

function wirePlayLedger() {
  const list = document.getElementById('log-list');
  const detail = document.getElementById('play-detail');
  if (!list || list.dataset.wired) return;
  list.dataset.wired = '1';

  const preview = (e) => {
    const b = e.target.closest && e.target.closest('.pl-move.has-read');
    if (b) showPlayDetail(+b.dataset.move, false);
  };
  const restore = () => {
    if (playPinned != null && playRows[playPinned]) showPlayDetail(playPinned, true);
    else detail.innerHTML = playDefaultDetail(true);
  };
  list.addEventListener('mouseover', preview);
  list.addEventListener('mouseout', restore);
  list.addEventListener('focusin', preview);
  list.addEventListener('focusout', restore);
  list.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.pl-move.has-read');
    if (!b) return;
    const idx = +b.dataset.move;
    playPinned = (playPinned === idx) ? null : idx;
    list.querySelectorAll('.pl-move.pinned').forEach((x) => x.classList.remove('pinned'));
    if (playPinned != null) { b.classList.add('pinned'); showPlayDetail(idx, true); }
    else detail.innerHTML = playDefaultDetail(true);
  });
}

// ---------- Floating taunts over the seats (kept out of The Play column) ----------
function renderBubbles(state) {
  const log = state.action_log || [];
  if (log.length < shownBubbleCount) shownBubbleCount = 0;
  log.slice(shownBubbleCount).forEach((e) => {
    if (e.taunt) showBubble(e.seat, e.taunt, state.num_players, e.trigger);
  });
  shownBubbleCount = log.length;
}

function showBubble(seat, text, numPlayers, trigger) {
  const container = document.getElementById('seats-container');
  if (!container || !container.children[seat]) return;
  const seatEl = container.children[seat];
  const old = seatEl.querySelector('.speech-bubble');
  if (old) old.remove();
  const bubble = document.createElement('div');
  const layout = layoutFor(numPlayers);
  const pos = layout[seat] || layout[layout.length - 1];
  const nearTop = pos && pos.t <= 32;
  bubble.className = 'speech-bubble'
    + (nearTop ? ' speech-bubble-below' : '')
    + (LOUD_TRIGGERS.has(trigger) ? ' is-loud' : '');
  bubble.innerText = text;
  seatEl.appendChild(bubble);
  clearTimeout(seatBubbleTimers[seat]);
  seatBubbleTimers[seat] = setTimeout(() => bubble.remove(), 6500);
}

function togglePanel(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('hidden');
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
wirePlayLedger();
loadPersonalities();

