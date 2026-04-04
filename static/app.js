let pollInterval = null;
let lastStateString = "";

const SUITS = ['♥', '♦', '♠', '♣'];
const RANKS = {14:'A', 13:'K', 12:'Q', 11:'J', 10:'T'};

function switchTab(tab) {
    document.getElementById('nav-play').classList.remove('active');
    document.getElementById('nav-arena').classList.remove('active');
    document.getElementById(`nav-${tab}`).classList.add('active');
    
    document.getElementById('tab-play').classList.add('hidden');
    document.getElementById('tab-arena').classList.add('hidden');
    document.getElementById(`tab-${tab}`).classList.remove('hidden');
}

function renderCard(cardStr, isBack=false) {
    if (isBack) return `<div class="card card-back"></div>`;
    let parsed = cardStr.replace(/[()\s]/g, '').split(',');
    if (parsed.length !== 2) return '';
    let rankInt = parseInt(parsed[0]);
    let suitInt = parseInt(parsed[1]);

    let rank = RANKS[rankInt] || rankInt.toString();
    let suit = SUITS[suitInt] || '?';
    let colorClass = (suit === '♥' || suit === '♦') ? 'red' : 'black';

    return `
        <div class="card ${colorClass}">
            <div class="card-top">${rank}${suit}</div>
            <div class="card-center">${suit}</div>
            <div class="card-bottom" style="transform: rotate(180deg)">${rank}${suit}</div>
        </div>
    `;
}

function startGame(opponent) {
    document.getElementById('start-overlay').classList.add('hidden');
    document.getElementById('villain-name').innerText = opponent;
    
    fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ opponent })
    }).then(() => {
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(pollState, 500);
    });
}

function pollState() {
    fetch('/api/state')
        .then(r => r.json())
        .then(data => updateUI(data))
        .catch(console.error);
}

function updateUI(state) {
    let currentStateString = JSON.stringify(state);
    if (currentStateString === lastStateString) return; 
    lastStateString = currentStateString;

    document.getElementById('pot-amount').innerText = '$' + state.pot.toFixed(2);
    document.getElementById('hero-stack').innerText = '$' + state.hero_stack.toFixed(2);
    document.getElementById('villain-stack').innerText = '$' + state.villain_stack.toFixed(2);

    document.getElementById('board-cards').innerHTML = state.board.map(c => renderCard(c)).join('');
    document.getElementById('hero-cards').innerHTML = state.hero_cards.map(c => renderCard(c)).join('');

    if (state.game_over && state.villain_cards.length > 0) {
        document.getElementById('villain-cards').innerHTML = state.villain_cards.map(c => renderCard(c)).join('');
    } else if (state.hero_cards.length > 0) {
        document.getElementById('villain-cards').innerHTML = renderCard('', true) + renderCard('', true);
    } else {
        document.getElementById('villain-cards').innerHTML = '';
    }

    const actionPanel = document.getElementById('action-panel');
    if (state.waiting_for_human) {
        let html = '';
        state.legal_actions.forEach(act => {
            let cls = act === 'FOLD' ? 'btn-fold' : (act.startsWith('BET') || act === 'ALL_IN' ? 'btn-bet' : 'btn-check-call');
            html += `<button class="action-btn ${cls}" onclick="sendAction('${act}')">${act.replace('_', ' ')}</button>`;
        });
        actionPanel.innerHTML = html;
        actionPanel.classList.add('active');
    } else {
        actionPanel.classList.remove('active');
    }

    if (state.game_over) {
        clearInterval(pollInterval);
        document.getElementById('game-over-overlay').classList.remove('hidden');
        let delta = state.last_result?.chip_delta[0] || 0;
        
        document.getElementById('outcome-title').innerText = delta > 0 ? "You Won!" : (delta < 0 ? "You Lost" : "Tie/Split");
        document.getElementById('outcome-details').innerText = `Result: ${state.last_result?.outcome} | Profit: ${delta > 0 ? '+' : ''}$${delta.toFixed(2)}`;
        
        // Render thoughts
        let thoughtsHtml = state.villain_thoughts.map(t => `<div class="thought-item">${t}</div>`).join('');
        if (!thoughtsHtml) thoughtsHtml = '<div class="thought-item" style="color:#64748b; border:none">Agent played instantly (no reasoning captured).</div>';
        document.getElementById('thoughts-list').innerHTML = thoughtsHtml;
    }
}

function sendAction(action) {
    document.getElementById('action-panel').classList.remove('active');
    fetch('/api/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
    });
}

function runSimulation() {
    const btn = document.getElementById('btn-simulate');
    const loading = document.getElementById('sim-loading');
    const results = document.getElementById('sim-results');
    
    let matchup = document.getElementById('sim-matchup').value;
    let hands = parseInt(document.getElementById('sim-hands').value) || 200;
    
    btn.disabled = true;
    results.classList.add('hidden');
    loading.classList.remove('hidden');
    
    fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matchup, hands })
    })
    .then(r => r.json())
    .then(data => {
        loading.classList.add('hidden');
        results.classList.remove('hidden');
        btn.disabled = false;
        
        let titleArgs = data.name.replace(' UI', '').split(' vs ');
        let a1 = titleArgs[0] || 'Agent 1';
        let a2 = titleArgs[1] || 'Agent 2';

        document.getElementById('res-winner').innerText = data.mean_chip_gain > 0 ? a1 : a2;
        document.getElementById('res-winrate').innerText = (data.win_rate * 100).toFixed(1) + "%";
        document.getElementById('res-tierate').innerText = (data.tie_rate * 100).toFixed(1) + "%";
        document.getElementById('res-time').innerText = data.elapsed.toFixed(1) + "s";
        
        // Break cache with timestamp
        if (data.plot_path) {
            document.getElementById('res-plot').src = `/${data.plot_path}?t=` + new Date().getTime();
        }
    })
    .catch(err => {
        console.error(err);
        loading.classList.add('hidden');
        btn.disabled = false;
        alert("Failed to run simulation");
    });
}
