/* Puzzle Workout — web app.
   Faithful port of src/fun_problem/quiz.py: random / leveled / adaptive
   sessions, lenient answer matching (normalized equality or numeric
   equivalence), coach's hints, and the honest source line.
   Zero dependencies; all text is inserted via textContent (no innerHTML). */
'use strict';

const $ = (id) => document.getElementById(id);

const DIFFICULTY_LABELS = {
  1: 'Foundational', 2: 'Developing', 3: 'Proficient', 4: 'Advanced', 5: 'Expert',
};

let PUZZLES = null;

/* ── answer matching (port of quiz.py) ───────────────────── */

function normalize(text) {
  return String(text).replace(/\s+/g, ' ').trim().toLowerCase();
}

/* Mirrors Python float(): sign, digits/underscores, decimal or exponent,
   plus inf/nan spellings. Returns null when Python would raise. */
function asNumber(text) {
  const s = String(text).trim();
  if (!/^[+-]?(?:(?:\d[\d_]*)(?:\.[\d_]*)?|\.\d[\d_]*|inf(?:inity)?|nan)(?:[eE][+-]?\d[\d_]*)?$/i.test(s)) {
    return null;
  }
  const t = s.replace(/_/g, '').toLowerCase();
  if (t.endsWith('inf') || t.endsWith('infinity')) return t.startsWith('-') ? -Infinity : Infinity;
  if (t.endsWith('nan')) return NaN;
  const v = Number(t);
  return Number.isNaN(v) ? null : v;
}

function answersMatch(attempt, answer, altAnswers) {
  const na = normalize(attempt);
  if (!na) return false;
  for (const candidate of [answer, ...(altAnswers || [])]) {
    if (na === normalize(candidate)) return true;
    const va = asNumber(na), vc = asNumber(normalize(candidate));
    if (va !== null && vc !== null && va === vc) return true;
  }
  return false;
}

/* ── bank helpers ────────────────────────────────────────── */

const bank = {
  questions(category, difficulty) {
    return PUZZLES.filter(q =>
      (!category || q.category === category) &&
      (!difficulty || q.difficulty === difficulty));
  },
  sample(n, category, difficulty) {
    const pool = [...this.questions(category, difficulty)];
    for (let i = pool.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [pool[i], pool[j]] = [pool[j], pool[i]];
    }
    return pool.slice(0, Math.max(0, n));
  },
};

/* ── session (port of QuizSession) ────────────────────────── */

class Session {
  constructor(mode, difficulty, category, limit) {
    this.mode = mode;
    this.limit = limit;
    this.category = category;
    this.currentDifficulty = mode === 'adaptive'
      ? (difficulty >= 1 && difficulty <= 5 ? difficulty : 2)
      : (difficulty || null);
    this.deck = (mode === 'random' || mode === 'leveled')
      ? bank.sample(limit, category, mode === 'leveled' ? difficulty : null)
      : [];
    this.used = new Set(this.deck.map(q => q.id));
    this.served = 0;
    this.attempted = 0;
    this.correct = 0;
    this.skipped = 0;
    this.current = null;
    this.outcomes = [];   // 'good' | 'bad' | 'skip' per served question
    this.hintUsed = 0;
  }

  drawAdaptive() {
    let pool = bank.questions(this.category, this.currentDifficulty)
      .filter(q => !this.used.has(q.id));
    if (!pool.length) {  // level exhausted → widen within the category
      pool = bank.questions(this.category).filter(q => !this.used.has(q.id));
    }
    if (!pool.length) return null;
    const q = pool[Math.floor(Math.random() * pool.length)];
    this.used.add(q.id);
    return q;
  }

  next() {
    if (this.served >= this.limit) return null;
    let q;
    if (this.mode === 'adaptive') {
      q = this.drawAdaptive();
      if (!q) return null;
    } else {
      if (this.served >= this.deck.length) return null;
      q = this.deck[this.served];
    }
    this.served += 1;
    this.current = q;
    return q;
  }

  submit(attempt) {
    this.attempted += 1;
    const ok = answersMatch(attempt, this.current.answer, this.current.alt_answers);
    if (ok) this.correct += 1;
    if (this.mode === 'adaptive') {
      this.currentDifficulty = Math.max(1, Math.min(5, this.currentDifficulty + (ok ? 1 : -1)));
    }
    return ok;
  }

  skip() { this.skipped += 1; }

  results() {
    return {
      served: this.served,
      attempted: this.attempted,
      correct: this.correct,
      skipped: this.skipped,
      accuracy: this.attempted ? this.correct / this.attempted : null,
      finalDifficulty: this.mode === 'adaptive' ? this.currentDifficulty : null,
    };
  }
}

/* ── rendering helpers ───────────────────────────────────── */

function prettyCategory(slug) {
  return slug.split('-').map(w => w[0].toUpperCase() + w.slice(1)).join(' ');
}

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

/* Question text: paragraphs on blank lines, <br> inside, short
   equation-like lines highlighted in mono. */
function renderQuestionText(container, text) {
  container.textContent = '';
  for (const para of String(text).split(/\n{2,}/)) {
    if (!para.trim()) continue;
    const p = el('p');
    para.split('\n').forEach((line, i) => {
      const trimmed = line.trim();
      if (i > 0) p.appendChild(document.createElement('br'));
      const isMath = trimmed.length <= 30 && /[+\-*/=×÷]/.test(trimmed) &&
        !/[.?!]$/.test(trimmed);
      p.appendChild(el('span', isMath ? 'q-math' : null, line));
    });
    container.appendChild(p);
  }
}

function sourceLine(q) {
  const s = q.source;
  if (s.kind === 'original') return 'Original puzzle composed for this project (MIT).';
  let line = 'Adapted from ' + s.title;
  if (s.author) line += ' by ' + s.author;
  if (s.year) line += ' (' + s.year + ')';
  return line + ' — ' + (s.license || 'public domain') + '.';
}

function sourceLineWithLink(q) {
  const base = sourceLine(q);
  if (!q.source.url) return base;
  return base + ' ' + q.source.url;
}

/* all-time solved counter */
function getAllTime() {
  return Number(localStorage.getItem('pw:solved') || '0') || 0;
}
function bumpAllTime() {
  try {
    localStorage.setItem('pw:solved', String(getAllTime() + 1));
  } catch (e) { /* storage unavailable — fine */ }
}

/* ── setup view ───────────────────────────────────────────── */

const setup = { mode: 'random', difficulty: 3, category: null, length: 10 };

function renderCategoryChips() {
  const wrap = $('catPicker');
  wrap.textContent = '';
  const counts = new Map();
  for (const q of PUZZLES) counts.set(q.category, (counts.get(q.category) || 0) + 1);

  const mk = (label, slug, n, pressed) => {
    const b = el('button', 'chip-btn');
    b.type = 'button';
    b.setAttribute('aria-pressed', pressed ? 'true' : 'false');
    b.appendChild(el('span', null, label));
    b.appendChild(el('span', 'n', String(n)));
    b.addEventListener('click', () => {
      setup.category = slug;
      [...wrap.children].forEach(c => c.setAttribute('aria-pressed', 'false'));
      b.setAttribute('aria-pressed', 'true');
      updateSetupNote();
    });
    wrap.appendChild(b);
  };
  mk('All categories', null, PUZZLES.length, true);
  for (const [slug, n] of [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    mk(prettyCategory(slug), slug, n, false);
  }
}

function updateSetupNote() {
  const note = $('setupNote');
  let poolSize;
  if (setup.mode === 'leveled') {
    poolSize = bank.questions(setup.category, setup.difficulty).length;
  } else {
    poolSize = bank.questions(setup.category).length;
  }
  const capped = Math.min(poolSize, setup.length);
  note.hidden = false;
  if (poolSize === 0) {
    note.textContent = 'No puzzles in that slice yet — try another level or category.';
  } else if (poolSize < setup.length) {
    note.textContent = poolSize + ' puzzle' + (poolSize === 1 ? '' : 's') +
      ' available in that slice — serving all of them.';
  } else {
    note.textContent = 'Drawing ' + setup.length + ' of ' + poolSize + ' puzzles, shuffled.';
  }
  $('startBtn').disabled = poolSize === 0;
}

function wireSetup() {
  for (const card of document.querySelectorAll('.mode-card input')) {
    card.addEventListener('change', () => {
      setup.mode = card.value;
      $('levelField').hidden = card.value !== 'leveled';
      if (card.value === 'leveled') setup.difficulty = selectedLevel();
      updateSetupNote();
    });
  }
  for (const seg of $('levelPicker').querySelectorAll('.seg')) {
    seg.addEventListener('click', () => {
      setup.difficulty = Number(seg.dataset.level);
      [...$('levelPicker').children].forEach(s => s.setAttribute('aria-pressed', String(s === seg)));
      updateSetupNote();
    });
  }
  for (const seg of $('lenPicker').querySelectorAll('.seg')) {
    seg.addEventListener('click', () => {
      setup.length = Number(seg.dataset.len);
      [...$('lenPicker').children].forEach(s => s.setAttribute('aria-pressed', String(s === seg)));
      updateSetupNote();
    });
  }
  $('startBtn').addEventListener('click', startSession);
}

function selectedLevel() {
  const on = $('levelPicker').querySelector('.seg[aria-pressed="true"]');
  return on ? Number(on.dataset.level) : 3;
}

/* ── play view ────────────────────────────────────────────── */

let session = null;
let phase = 'ask';            // 'ask' | 'review'
let revealed = false;

function startSession() {
  session = new Session(setup.mode, setup.mode === 'leveled' ? selectedLevel() : null,
    setup.category, setup.length);
  phase = 'ask';
  $('setupView').hidden = true;
  $('doneView').hidden = true;
  $('playView').hidden = false;
  renderDots();
  nextQuestion();
  $('playView').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderDots() {
  const wrap = $('qDots');
  wrap.textContent = '';
  const n = Math.max(session.limit, session.outcomes.length);
  for (let i = 0; i < n; i++) {
    const d = el('span', 'dot');
    const st = session.outcomes[i];
    if (st) d.classList.add(st);
    else if (i === session.outcomes.length) d.classList.add('current');
    wrap.appendChild(d);
  }
}

function updateMeter() {
  const meter = $('levelMeter');
  meter.hidden = session.mode !== 'adaptive';
  if (session.mode !== 'adaptive') return;
  const lvl = session.currentDifficulty;
  $('meterLabel').textContent = 'Level ' + lvl + ' · ' + DIFFICULTY_LABELS[lvl];
  $('meterFill').style.width = (lvl / 5 * 100) + '%';
}

function nextQuestion() {
  const q = session.next();
  if (!q) return finishSession();
  phase = 'ask';
  revealed = false;
  $('qProgress').textContent = 'Question ' + session.served + ' of ' + session.limit;
  $('qCat').textContent = prettyCategory(q.category);
  $('qDiff').textContent = DIFFICULTY_LABELS[q.difficulty];
  $('qId').textContent = q.id;
  renderQuestionText($('qText'), q.question);

  $('answerRow').hidden = false;
  document.querySelector('.input-hint').hidden = false;
  $('checkBtn').hidden = false;
  const input = $('answerInput');
  input.value = '';
  input.disabled = false;
  if (window.matchMedia('(pointer: fine)').matches) input.focus();

  $('hintBtn').hidden = false;
  $('hintBtn').textContent = '\u24D8 Show the coach\u2019s hint';
  $('hintPanel').hidden = true;
  $('verdict').hidden = true;
  $('verdict').className = 'verdict';
  $('skipBtn').hidden = false;
  $('revealBtn').hidden = false;
  $('nextBtn').hidden = true;
  renderDots();
  updateMeter();
}

function submitAnswer() {
  if (phase !== 'ask') return;
  const attempt = $('answerInput').value;
  if (!normalize(attempt)) return;                 // empty → keep waiting
  const ok = session.submit(attempt);
  session.outcomes.push(ok ? 'good' : 'bad');
  if (ok) bumpAllTime();
  showVerdict(ok ? 'ok' : 'no', ok ? 'Got it.' : 'Not quite.');
  renderDots();
  updateMeter();
}

function revealAnswer() {
  if (phase !== 'ask') return;
  session.outcomes.push('skip');                  // revealed = not attempted
  session.skip();
  showVerdict('rev', 'Revealed.');
  renderDots();
  updateMeter();
}

function skipQuestion() {
  if (phase !== 'ask') return;
  session.outcomes.push('skip');
  session.skip();
  nextQuestion();
}

function showVerdict(kind, headline) {
  phase = 'review';
  const q = session.current;
  const v = $('verdict');
  v.hidden = false;
  v.className = 'verdict ' + kind;
  $('verdictLine').textContent = headline;
  $('theAnswer').textContent = q.answer;
  $('theExplanation').textContent = q.explanation;
  $('theSource').textContent = sourceLineWithLink(q);

  const input = $('answerInput');
  input.disabled = true;
  $('checkBtn').hidden = true;
  $('hintBtn').hidden = true;
  $('revealBtn').hidden = true;
  $('skipBtn').hidden = true;
  $('nextBtn').hidden = false;
  document.querySelector('.input-hint').hidden = true;
  $('nextBtn').focus();
}

function finishSession() {
  const r = session.results();
  $('playView').hidden = true;
  $('doneView').hidden = false;

  const head = { random: 'Workout done.', leveled: 'Level drilled.', adaptive: 'Found your edge.' }[session.mode];
  $('resultsHead').textContent = head;
  $('accuracyNum').textContent = r.accuracy === null ? '—'
    : String(Math.round(r.accuracy * 100));

  const grid = $('resultsGrid');
  grid.textContent = '';
  const rows = [
    ['Served', r.served],
    ['Attempted', r.attempted],
    ['Correct', r.correct],
    ['Skipped', r.skipped],
  ];
  if (r.finalDifficulty !== null) {
    rows.push(['Final level', r.finalDifficulty + ' · ' + DIFFICULTY_LABELS[r.finalDifficulty]]);
  }
  for (const [k, val] of rows) {
    grid.appendChild(el('dt', null, k));
    grid.appendChild(el('dd', null, String(val)));
  }

  const total = getAllTime();
  const note = $('allTimeNote');
  note.hidden = false;
  note.textContent = total === 0
    ? 'First correct answers on this device will tally here \u2014 nothing leaves your browser.'
    : 'That\u2019s ' + total + ' puzzle' + (total === 1 ? '' : 's') + ' solved all-time on this device.';

  $('doneView').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ── warm-up card ─────────────────────────────────────────── */

function renderWarmup() {
  const body = $('warmupBody');
  body.textContent = '';
  const pool = PUZZLES.filter(q => q.difficulty <= 2);
  const q = pool[Math.floor(Math.random() * pool.length)];

  const wrap = el('div');
  const qm = el('div', 'q-mini');
  renderQuestionText(qm, q.question);
  wrap.appendChild(el('p', 'q-meta',
    prettyCategory(q.category) + ' · ' + DIFFICULTY_LABELS[q.difficulty]));
  wrap.appendChild(qm);

  const form = el('form');
  const input = el('input');
  input.type = 'text';
  input.autocomplete = 'off';
  input.spellcheck = false;
  input.placeholder = 'Your answer\u2026';
  input.setAttribute('aria-label', 'Your answer');
  const btn = el('button', 'btn primary', 'Check');
  btn.type = 'submit';
  form.appendChild(input);
  form.appendChild(btn);
  wrap.appendChild(form);

  const actions = el('div', 'warm-actions');
  const reveal = el('button', 'textbtn', 'Reveal the answer');
  reveal.type = 'button';
  actions.appendChild(reveal);
  const hintBtn = el('button', 'textbtn', '\u24D8 Coach\u2019s hint');
  hintBtn.type = 'button';
  actions.appendChild(hintBtn);
  wrap.appendChild(actions);

  const hintPanel = el('p', 'explain-mini');
  hintPanel.hidden = true;
  wrap.appendChild(hintPanel);

  let done = false;
  function settle(ok) {
    if (done) return;
    done = true;
    form.remove();
    hintBtn.remove();
    reveal.remove();
    hintPanel.hidden = true;
    const verdict = el('p', 'verdict-mini ' + (ok ? 'ok' : 'no'),
      ok ? 'Got it — nice warm-up.' : 'Answer: ' + q.answer);
    wrap.appendChild(verdict);
    wrap.appendChild(el('p', 'explain-mini', q.explanation));
    wrap.appendChild(el('p', 'src-mini', sourceLine(q)));
    const go = el('button', 'btn primary', 'Start a full workout \u2192');
    go.type = 'button';
    go.addEventListener('click', () => {
      $('workout').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    wrap.appendChild(go);
  }
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (done) return;
    const attempt = input.value;
    if (!normalize(attempt)) { input.focus(); return; }
    settle(answersMatch(attempt, q.answer, q.alt_answers));
  });
  reveal.addEventListener('click', () => settle(false));
  hintBtn.addEventListener('click', () => {
    hintPanel.textContent = q.guidance;
    hintPanel.hidden = false;
  });

  body.appendChild(wrap);
}

/* ── provenance list ──────────────────────────────────────── */

function renderProvenance() {
  const list = $('provList');
  list.textContent = '';
  const groups = new Map();
  for (const q of PUZZLES) {
    const s = q.source;
    const key = s.kind === 'original' ? 'original' : (s.author || s.title || 'Anonymous');
    if (!groups.has(key)) groups.set(key, { kind: s.kind, who: key, n: 0, title: s.title });
    groups.get(key).n += 1;
  }
  const entries = [...groups.values()].sort((a, b) => {
    if ((a.kind === 'original') !== (b.kind === 'original')) return a.kind === 'original' ? -1 : 1;
    return b.n - a.n;
  });
  for (const g of entries) {
    const li = el('li');
    li.appendChild(el('span', 'who', g.kind === 'original' ? 'Original compositions' : g.who));
    li.appendChild(el('span', 'what',
      g.kind === 'original' ? 'Written for this project \u2014 MIT licensed.' : g.title));
    li.appendChild(el('span', 'count', String(g.n)));
    list.appendChild(li);
  }
}

/* ── keyboard (CLI parity: h = hint, s = skip) ─────────────── */

document.addEventListener('keydown', (e) => {
  if ($('playView').hidden) return;
  const typing = /^(input|textarea)$/i.test(e.target.tagName);
  if (e.key === 'Enter') {
    if (typing && phase === 'ask') { e.preventDefault(); submitAnswer(); }
    else if (!typing && phase === 'review') { e.preventDefault(); $('nextBtn').click(); }
    return;
  }
  if (typing) return;
  if (e.key === 'h' || e.key === 'H') {
    if (phase === 'ask' && $('hintPanel').hidden) $('hintBtn').click();
  } else if (e.key === 's' || e.key === 'S') {
    if (phase === 'ask') skipQuestion();
  }
});

/* ── boot ─────────────────────────────────────────────────── */

async function boot() {
  $('hintBtn').addEventListener('click', () => {
    const panel = $('hintPanel');
    if (panel.hidden) {
      panel.hidden = false;
      $('hintText').textContent = session.current.guidance;
      $('hintBtn').textContent = '\u24D8 Hide the coach\u2019s hint';
    } else {
      panel.hidden = true;
      $('hintBtn').textContent = '\u24D8 Show the coach\u2019s hint';
    }
  });
  $('checkBtn').addEventListener('click', submitAnswer);
  $('revealBtn').addEventListener('click', revealAnswer);
  $('skipBtn').addEventListener('click', skipQuestion);
  $('nextBtn').addEventListener('click', () => {
    if (phase === 'review') nextQuestion();   // never advance mid-question
  });
  $('againBtn').addEventListener('click', startSession);
  $('newSettingsBtn').addEventListener('click', () => {
    $('doneView').hidden = true;
    $('setupView').hidden = false;
    updateSetupNote();
  });

  wireSetup();
  try {
    const res = await fetch('puzzles.json');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    PUZZLES = await res.json();
    if (!Array.isArray(PUZZLES) || !PUZZLES.length) throw new Error('empty bank');
  } catch (err) {
    $('warmupBody').textContent = 'Couldn\u2019t load the puzzle bank (' + err.message + '). ' +
      'Refresh to try again.';
    $('setupNote').hidden = false;
    $('setupNote').textContent = 'The puzzle bank failed to load \u2014 refresh the page.';
    return;
  }
  renderCategoryChips();
  renderWarmup();
  renderProvenance();
  updateSetupNote();
  const start = $('startBtn');
  start.disabled = false;
  start.textContent = 'Start the workout';
}

boot();