// ---------------------------------------------------------------------------
// Bluff & Bayes — engraved bot portraits (the "silhouettes").
//
// One authored line-engraving per player in the roster, drawn in a single
// consistent stroke weight so the seven read as one set. `currentColor` carries
// the ink, so the same mark sits as ink-on-paper in the roster and bone-on-baize
// at the table. No emoji anywhere in the UI — these replace them.
//
// Purely presentational. Nothing here touches decision logic or game state.
// ---------------------------------------------------------------------------

(function (global) {
  'use strict';

  const VB = '0 0 96 112';
  const S = 'fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"';
  const INK = 'fill="currentColor"';

  // Each entry: a short human label (for aria) + the inner SVG markup.
  const FIGURES = {
    // Jester — two-belled cap, tilted head, diamond ruff. A pointed silhouette.
    'wildcard': {
      label: 'Wildcard, a jester',
      svg: `
        <g ${S}>
          <path d="M40 44c0-13 18-13 18 0 0 10-6 17-9 17s-9-7-9-17Z"/>
          <path d="M40 40c-4-9-12-14-22-16 2 9 6 15 12 19"/>
          <path d="M58 40c5-9 14-14 24-16-1 9-6 15-12 19"/>
          <path d="M35 62c4 5 8 7 14 7s10-2 14-7"/>
          <path d="M31 74l7-6 7 6 7-6 7 6 7-6"/>
          <path d="M33 82l30 0-4 20-22 0-4-20Z"/>
        </g>
        <circle cx="16" cy="24" r="3.4" ${INK}/>
        <circle cx="82" cy="24" r="3.4" ${INK}/>
        <circle cx="48" cy="90" r="2.2" ${INK}/>
        <circle cx="43" cy="52" r="1.6" ${INK}/>
        <circle cx="55" cy="52" r="1.6" ${INK}/>`
    },

    // The Rock — a faceted monolith on a flat base. Blocky, immovable.
    'the-rock': {
      label: 'The Rock, a standing stone',
      svg: `
        <g ${S}>
          <path d="M28 96l-4-46 16-24 26 4 8 30-6 36-40 0Z"/>
          <path d="M40 26l6 32-14 8"/>
          <path d="M52 30l16 4-10 24 10 14"/>
          <path d="M46 58l12 4"/>
          <path d="M18 98l60 0"/>
        </g>
        <path d="M34 44l5-3 4 5-5 3-4-5Z" ${INK}/>`
    },

    // Calling Station — a candlestick telephone. Sees one more card, always.
    'calling-station': {
      label: 'Calling Station, a candlestick telephone',
      svg: `
        <g ${S}>
          <path d="M40 30h16l-3 8h-10l-3-8Z"/>
          <ellipse cx="48" cy="28" rx="12" ry="4"/>
          <path d="M46 38l4 34"/>
          <path d="M38 96c0-12 20-12 20 0"/>
          <path d="M30 96h36"/>
          <path d="M56 44c14 0 18 10 18 18l0 10"/>
          <ellipse cx="74" cy="74" rx="7" ry="4" transform="rotate(20 74 74)"/>
          <path d="M40 52c-10 2-14 8-14 16"/>
        </g>
        <circle cx="26" cy="70" r="2.4" ${INK}/>`
    },

    // The Mathematician — open dividers scribing an arc over tick marks.
    'the-mathematician': {
      label: 'The Mathematician, a pair of dividers',
      svg: `
        <g ${S}>
          <circle cx="48" cy="24" r="5"/>
          <path d="M45 28L30 92"/>
          <path d="M51 28L66 84"/>
          <path d="M66 84l-4 8 8-2"/>
          <path d="M30 92l-3 8"/>
          <path d="M24 78c14 12 34 12 48 0"/>
        </g>
        <path d="M26 96l0 6M36 96l0 6M46 96l0 6M56 96l0 6M66 96l0 6" ${S}/>`
    },

    // The Maniac — a lit keg, fuse curling to a flame, sparks flying.
    'the-maniac': {
      label: 'The Maniac, a lit powder keg',
      svg: `
        <g ${S}>
          <path d="M30 66a18 18 0 1 0 36 0 18 18 0 0 0-36 0Z"/>
          <path d="M48 48c2-10-2-16-2-16"/>
          <path d="M46 32c-4-6-2-12 2-16 2 5 6 7 6 12s-4 6-4 10"/>
          <path d="M36 60c4 4 6 10 4 16"/>
        </g>
        <path d="M50 16c1-4 4-7 4-7s0 5 3 7-3 3-3 6-4-2-4-9Z" ${INK}/>
        <path d="M20 44l8 4M18 62l9 0M24 82l7-5M72 44l-8 4M76 62l-9 0M70 82l-7-5" ${S}/>`
    },

    // The Profiler — deerstalker head in profile, magnifier to the eye.
    'the-profiler': {
      label: 'The Profiler, a detective with a magnifier',
      svg: `
        <g ${S}>
          <path d="M30 44c0-16 26-18 30-4 2 8 0 16-4 22-2 4-2 10 0 14l-22 0c2-8-4-14-4-22v-10Z"/>
          <path d="M28 40c-6-4-10-4-14-2 4-6 10-8 16-8"/>
          <path d="M60 40c6-4 10-4 14-2-4-6-10-8-16-8"/>
          <path d="M30 34c8-6 22-6 30 0"/>
          <circle cx="60" cy="60" r="9"/>
          <path d="M67 67l12 14"/>
        </g>
        <circle cx="42" cy="56" r="2" ${INK}/>`
    },

    // The Data Scientist — an automaton head; a plotted curve on its face panel.
    'the-data-scientist': {
      label: 'The Data Scientist, an automaton',
      svg: `
        <g ${S}>
          <path d="M30 40h36v44a6 6 0 0 1-6 6H36a6 6 0 0 1-6-6V40Z"/>
          <path d="M48 40V28"/>
          <path d="M34 96l0 8M62 96l0 8"/>
          <rect x="37" y="50" width="22" height="16" rx="2"/>
          <path d="M39 62c4-2 6-8 9-8s5 6 9 4"/>
          <path d="M30 54h-6M30 66h-6M66 54h6M66 66h6"/>
        </g>
        <circle cx="48" cy="24" r="3.6" ${INK}/>
        <circle cx="38" cy="76" r="2" ${INK}/>
        <circle cx="48" cy="76" r="2" ${INK}/>
        <circle cx="58" cy="76" r="2" ${INK}/>`
    },

    // You — an empty captain's chair. Your seat at the table.
    'human': {
      label: 'Your seat, an empty chair',
      svg: `
        <g ${S}>
          <path d="M30 34c0-6 36-6 36 0"/>
          <path d="M30 34v30M66 34v30"/>
          <path d="M37 34v26M45 34v26M53 34v26M59 34v26"/>
          <path d="M26 64h44l-3 12H29l-3-12Z"/>
          <path d="M30 76l-4 24M66 76l4 24"/>
          <path d="M34 88h28"/>
        </g>`
    }
  };

  const FALLBACK = {
    label: 'A player',
    svg: `<g ${S}><circle cx="48" cy="40" r="14"/><path d="M24 92c0-16 48-16 48 0"/></g>`
  };

  /**
   * Return an inline <svg> string for a roster key.
   * @param {string} key   personality slug, or "human"
   * @param {object} [opt] { title?:string }  extra accessible name context
   */
  function botMark(key, opt) {
    const fig = FIGURES[key] || FALLBACK;
    const name = (opt && opt.title) ? opt.title : fig.label;
    return `<svg class="bot-mark" viewBox="${VB}" role="img" aria-label="${name}" focusable="false">${fig.svg}</svg>`;
  }

  // Small engraved marks for the game-over card (trophy / skull / farewell hand).
  const OUTCOME_MARKS = {
    'human_wins': `<svg class="outcome-mark" viewBox="0 0 96 96" role="img" aria-label="Trophy" focusable="false">
        <g ${S}><path d="M30 20h36v14c0 12-8 20-18 20S30 46 30 34V20Z"/>
        <path d="M30 26c-10 0-14-6-14-12h14M66 26c10 0 14-6 14-12H66"/>
        <path d="M48 54v14M36 78h24l-3-10H39l-3 10Z"/><path d="M30 84h36"/></g></svg>`,
    'human_busted': `<svg class="outcome-mark" viewBox="0 0 96 96" role="img" aria-label="Out of chips" focusable="false">
        <g ${S}><path d="M28 44a20 20 0 1 1 40 0c0 8-4 12-4 18H32c0-6-4-10-4-18Z"/>
        <path d="M40 74h16M40 82h16"/></g>
        <circle cx="40" cy="44" r="4" ${INK}/><circle cx="56" cy="44" r="4" ${INK}/></svg>`,
    'default': `<svg class="outcome-mark" viewBox="0 0 96 96" role="img" aria-label="Table closed" focusable="false">
        <g ${S}><path d="M24 60c8-10 16-14 24-14s16 4 24 14"/><path d="M30 66c6-6 12-9 18-9s12 3 18 9"/>
        <path d="M48 40V22M40 30l8-8 8 8"/></g></svg>`
  };
  function outcomeMark(reason) {
    return OUTCOME_MARKS[reason] || OUTCOME_MARKS['default'];
  }

  // A tick drawn in the same engraving stroke as the portraits — never a glyph.
  function tick(cls) {
    return `<svg class="${cls || 'ink-tick'}" viewBox="0 0 16 16" role="img" aria-label="selected" focusable="false">`
      + `<path d="M3 8.5 L6.5 12 L13 4" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }

  global.BnB = global.BnB || {};
  global.BnB.botMark = botMark;
  global.BnB.outcomeMark = outcomeMark;
  global.BnB.tick = tick;
})(window);
