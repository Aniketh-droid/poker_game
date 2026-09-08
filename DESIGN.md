---
name: Bluff & Bayes
description: A private card room kept as a hand-inked ledger — a running account of play against inspectable AI opponents.
colors:
  baize: "#142019"
  baize-deep: "#0e1712"
  baize-well: "#0b120e"
  plate: "#182a20"
  paper: "#ece3cf"
  paper-shade: "#e3d7bc"
  paper-edge: "#d8caa9"
  ink: "#211d16"
  ink-soft: "#4b4335"
  bone: "#efe7d4"
  bone-2: "#dbcfb4"
  bone-dim: "#c3b596"
  oxblood: "#5c2a2f"
  oxblood-bright: "#7c3a37"
  oxblood-deep: "#3d1c20"
  brass-deep: "#7d5f30"
  ledger-rule: "rgba(54,72,104,0.22)"
  ledger-rule-strong: "rgba(54,72,104,0.40)"
  gain-green: "#2f5233"
  card-face: "#f7f0dd"
  card-red: "#8a2b2b"
typography:
  display:
    fontFamily: "'Caslon Display', 'Caslon Text', Georgia, serif"
    fontSize: "clamp(2rem, 6vw, 3.4rem)"
    fontWeight: 400
    lineHeight: 1.04
    letterSpacing: "0.01em"
  headline:
    fontFamily: "'Caslon Display', 'Caslon Text', Georgia, serif"
    fontSize: "clamp(1.4rem, 3.4vw, 1.9rem)"
    fontWeight: 400
    lineHeight: 1.15
  title:
    fontFamily: "'Caslon Display', 'Caslon Text', Georgia, serif"
    fontSize: "1.5rem"
    fontWeight: 400
    lineHeight: 1.15
  body:
    fontFamily: "'Caslon Text', Georgia, 'Times New Roman', serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.5
  body-italic:
    fontFamily: "'Caslon Text', Georgia, serif"
    fontSize: "0.9rem"
    fontWeight: 400
    lineHeight: 1.32
    letterSpacing: "normal"
  label:
    fontFamily: "'Franklin', 'Helvetica Neue', Arial, sans-serif"
    fontSize: "0.72rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.16em"
  figure:
    fontFamily: "'Franklin', 'Helvetica Neue', Arial, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 600
    lineHeight: 1.3
    fontFeature: "tabular-nums"
rounded:
  hairline: "1px"
  stamp: "2px"
  card: "3px"
  ellipse: "50% / 46%"
spacing:
  hair: "6px"
  xs: "10px"
  sm: "16px"
  md: "22px"
  lg: "30px"
  xl: "34px"
  rule: "32px"
components:
  button-primary:
    backgroundColor: "{colors.oxblood}"
    textColor: "{colors.bone}"
    typography: "{typography.label}"
    rounded: "{rounded.stamp}"
    padding: "15px 30px"
  button-primary-hover:
    backgroundColor: "{colors.oxblood-bright}"
    textColor: "{colors.bone}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.bone-2}"
    typography: "{typography.label}"
    rounded: "{rounded.stamp}"
    padding: "11px 20px"
  button-bet:
    backgroundColor: "{colors.oxblood}"
    textColor: "{colors.bone}"
    typography: "{typography.label}"
    rounded: "{rounded.stamp}"
    padding: "13px 20px"
  seat-count-stamp:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.stamp}"
    padding: "12px 8px 10px"
  seat-count-stamp-active:
    backgroundColor: "{colors.oxblood}"
    textColor: "{colors.bone}"
  ledger-sheet:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.stamp}"
    padding: "32px 30px 34px"
  playing-card:
    backgroundColor: "{colors.card-face}"
    textColor: "{colors.ink}"
    typography: "{typography.display}"
    rounded: "{rounded.card}"
    padding: "4px 6px"
    width: "54px"
    height: "76px"
---

# Design System: Bluff & Bayes

## Overview

**Creative North Star: "The Card-Room Ledger"**

The whole app reads as a hand-inked ledger kept by a private card room. A match is not a session that resets — it is a running account, written down. The screen is a bone ledger sheet ruled in faint blue with an oxblood margin rule, laid on a deep baize ground. The live poker table is an engraved plate tipped into that page: a dark inked plate with a drawn double-rule frame and a real cast shadow, not a felt oval with a floating chat panel. The running account (hand number, stack, session profit/loss) is the persistent spine at the top of the page; the hand's moves are a bound ruled column; each opponent's reasoning opens as a margin note beside it.

Everything that would be metal in a casino is drawn instead of rendered: rails, blind discs, bet marks, ticks and portrait medallions are single-stroke ink linework in one consistent hand. There are no gloss gradients, no inset bevels, no imitation brass, no glass, no glow, no gradient text, no drop-shadow halos, and no zero-offset coloured shadow anywhere. Brass survives only as a flat sepia keyline (`#7d5f30`). Colour is never the only signal for a state — every table state also carries a shape, a label, or a drawn mark. Motion is almost absent: one authored moment, the post-hand result "leaf" turning in the account.

The voice is set in Libre Caslon (Display for names, headings and the pot; Text for reading and for italic taunts and action words). Figures, labels and buttons are Libre Franklin, small-caps-tracked. The result must feel like a real room a visitor is joining — characterful and warm, never sterile fintech, never casino neon.

**Key Characteristics:**
- Bone ledger paper on deep baize; oxblood leather for bindings and primary action
- All "metal" is drawn ink linework, one consistent stroke
- The table is a physical engraved plate with an offset+blur cast shadow
- Caslon for voice, Franklin for figures and labels
- Every state cue is redundant with shape, label or mark — never colour alone
- Near-zero motion; full `prefers-reduced-motion` coverage

## Colors

A warm, low-chroma palette of paper, ink, baize green and oxblood leather, with a single muted sepia keyline and two reserved semantic hues for money.

### Primary
- **Oxblood Leather** (`#5c2a2f`, bright `#7c3a37`, deep `#3d1c20`): the binding and the acting hand. Used for the topnav band, the setup header band, the hero rail, primary and bet buttons (flat fill), active table-size stamps, the selected-row spine, "To act" / "Mucked" / "All in" tags, blind (BB) discs, street "now" pill, and session-loss figures. Bright is the hover state; deep is the border and the 2px printed edge under buttons.
- **Ledger Bone / Paper** (`#ece3cf`, shade `#e3d7bc`, edge `#d8caa9`): every writing surface — setup cards, the full-bleed game page, overlay card, floating taunt scraps, the margin-note panel. Warm card face is a lighter bone (`#f7f0dd`).

### Secondary
- **Baize Green** (`#142019`, deep `#0e1712`, well `#0b120e`): the room ground behind the paper, carrying a faint woven `repeating-linear-gradient` texture and a vignette. `--plate` (`#182a20`) is the darker engraved-plate field of the table.

### Tertiary
- **Brass Sepia** (`#7d5f30`): a single flat keyline weight only — the hairline ring around roster portrait medallions. No gradient, no bevel, no fill.

### Neutral
- **Ink** (`#211d16`) / **Soft Ink** (`#4b4335`): body text and linework on paper; soft ink for secondary text, the double-rule dividers, and SB discs.
- **Bone tints** (`#efe7d4`, `#dbcfb4`, `#c3b596`): text and linework on dark surfaces — `--bone` for primary, `--bone-2` for secondary, `--bone-dim` for muted / "reading…" states.
- **Ledger rule blue** (`rgba(54,72,104,0.22)`, strong `0.40`): the horizontal ruling on paper and all faint hairline dividers. Never used for text.
- **Margin rule** (`#7c3a37`): the vertical oxblood rule drawn ~44px in on every ledger sheet (~18px on narrow screens).

### Named Rules
**The Drawn-Metal Rule.** Anything that would be metal in a casino — rails, counters, discs, bet marks, ticks — is single-stroke ink linework in the portrait hand. No gloss gradient, no inset bevel, no imitation brass fill. Brass appears only as the flat `#7d5f30` keyline.

**The Reserved-Money Rule.** `#2f5233` (gain green) and oxblood mark session/hand outcome up and down. These two hues carry money direction only; do not spend them on chrome or decoration.

**The Colour-Is-Never-Alone Rule.** Every state that uses colour also carries a shape, a label, or a drawn mark. A red-free reader must be able to tell turn, folded, all-in, street and button apart.

## Typography

**Display Font:** Libre Caslon Display, mapped to `'Caslon Display'` (fallback `'Caslon Text'`, Georgia, serif) — self-hosted, one weight (400).
**Body Font:** Libre Caslon Text, mapped to `'Caslon Text'` (fallback Georgia, Times New Roman, serif) — self-hosted, 400 roman, 400 italic, 700.
**Label / Figure Font:** Libre Franklin, mapped to `'Franklin'` (fallback Helvetica Neue, Arial, sans-serif) — self-hosted variable face (100–900).

**Character:** A period-correct Caslon for everything with a voice — names, headings, the pot figure, and italic asides — against a crisp grotesque for the countable and the operational. The serif is the room talking; the sans is the ledger's ruled columns.

### Hierarchy
- **Display** (Caslon Display 400, `clamp(2rem, 6vw, 3.4rem)`, line-height 1.04): the setup hero headline only ("Pull up a seat.").
- **Headline** (Caslon Display 400, `clamp(1.4rem, 3.4vw, 1.9rem)`, 1.15): the result-leaf title and game-over heading.
- **Title** (Caslon Display 400, `1.5rem`, 1.15): the ledger-head "The Card Room" spine title; the pot amount runs slightly larger at `1.6rem`.
- **Body** (Caslon Text 400, `17px` / `16px` on small screens, 1.5): reading text, setup paragraph (max ~56ch), the margin-note read.
- **Body italic** (Caslon Text italic, `~0.86–0.9rem`): taglines, roster style claims, floating taunts, action words in "The Play" column, waiting notes, the hero's name.
- **Label** (Franklin 700, `~0.6–0.74rem`, letter-spacing `0.12–0.22em`, UPPERCASE): section labels, figure captions ("Your stack"), street pips, button text, state tags. Tracking widens as the label shrinks.
- **Figure** (Franklin 600, tabular-nums): all stacks, pot, session P/L, bet chips. Always `font-variant-numeric: tabular-nums`.

### Named Rules
**The Two-Hands Rule.** Caslon carries voice (names, headings, pot, italic taunts and action words). Franklin carries the countable and the operational (figures, labels, buttons, state tags). Nothing crosses over.

**The Tabular-Money Rule.** Every number that can change during play is set in Franklin with `tabular-nums` so columns of figures stay aligned as they update in place.

**The Tracked-Caps Rule.** Franklin labels are uppercase and letter-spaced (`0.12em` at title sizes up to `0.22em` for the pot cap). Lowercase Franklin is not used for labels.

## Layout

A single centred page column, `max-width: 1160px`, with fluid gutters (`clamp(14px, 4vw, 28px)`) and generous bottom padding. The sticky oxblood topnav sits above it.

**Setup screen:** an oxblood header band (full-bleed within the column, square corners) followed by stacked ledger-sheet cards. The roster is a ruled list — one player per `56px | 1fr | 15.5rem | 24px` grid row (portrait, name+claim, model tell in a bordered column, checkbox). Below ~720px the model tell drops to a third row and the margin rule pulls in to ~18px.

**Game screen:** one full-bleed ledger page (border and shadow stripped from the sheet). The running-account spine (`.ledger-head`) sits under a `3px double` ink rule. The body is a `1fr | 296px` grid — the engraved-plate table over the hero rail on the left, "The Play" column on the right, divided by a hairline. Below ~1000px the column drops under the table with a `3px double` rule between them.

**The table:** an absolutely-positioned ellipse (`aspect-ratio: 16 / 9.2` on desktop, `1 / 1.18` portrait on phones), `width: min(100%, 860px)`. Seats are absolutely placed and updated in place — never rebuilt on poll.

**Spacing rhythm:** the ledger's horizontal rule is every **32px**; vertical rhythm and panel padding track that (component padding clusters at 6 / 10 / 16 / 22 / 30 / 34px). The hero rail and result leaf deliberately bleed to the page edges via negative margins (`-26px` / `-34px`).

## Elevation & Depth

Depth is drawn, not lit. The system is flat except for one structural cast shadow: the engraved-plate table reads as a real object dropped onto the page, using an **offset + blur** shadow. Ledger sheets on the baize ground carry a matching drop shadow plus a thin inset top highlight and bottom shade to sit as paper on cloth. Nothing lifts on hover — buttons nudge `translateY(±1px)` with no shadow bloom. There is no glow and no zero-offset coloured shadow anywhere; the acting seat is marked with an outline and a label, not a halo.

### Shadow Vocabulary
- **Sheet drop** (`box-shadow: 0 8px 15px rgba(0,0,0,0.4), 0 2px 4px rgba(0,0,0,0.36)`): a ledger sheet resting on the baize ground (setup cards, overlay card). Paired with `inset 0 1px 0 rgba(255,255,255,0.5)` and `inset 0 -2px 0 rgba(140,110,60,0.18)`.
- **Plate cast** (`box-shadow: 0 10px 22px rgba(0,0,0,0.35), 0 3px 6px rgba(0,0,0,0.3)`): the table plate tipped into the page.
- **Set shadow** (`box-shadow: 0 5px 12px rgba(0,0,0,0.34)`): small objects seated on the plate (medallions, scraps).
- **Field well** (`inset 0 6px 22px rgba(0,0,0,0.5)`): the sunken playing field inside the plate.

### Named Rules
**The Flat-Except-The-Table Rule.** Surfaces are flat at rest. The only structural shadow is the one that makes the table a physical plate on the page. State (hover, focus, acting) is shown by outline, position or label — never by a new shadow.

**The No-Halo Rule.** No glow, no zero-offset coloured shadow, no drop-shadow halo — especially not on the acting seat, which is marked by a bone outline plus a "To act" tag.

## Shapes

Corners are effectively square: `1px` for keylines and inked stamps, `2px` for buttons, cards, sheets and checkboxes, `3px` for playing cards. Nothing is soft. The two curved forms are deliberate and specific: the **portrait oval** (a true vertical ellipse, taller than wide — `54×62` at the table, `46×54` in the roster — framed by a double inner keyline) and the **table ellipse** (`border-radius: 50% / 46%`, echoed by its inner double rule and sunken field). Borders are hairlines: `1px` / `1.5px` ink or bone rules, `3px double` ink rules for major section breaks, `1px dotted` under interactive move rows. The recurring silhouette is the ruled sheet — a horizontal-line field with one vertical margin rule.

## Components

### Buttons
- **Shape:** square-ish inked stamp (`2px` radius), Franklin 700 uppercase, letter-spacing `0.12–0.16em`.
- **Primary** (`.btn-primary`): flat oxblood fill (`#5c2a2f`), bone text, `1px` oxblood-deep border, `15px 30px` padding, a hard `0 2px 0` oxblood-deep printed edge. Hover → oxblood-bright + `translateY(-1px)`; active → `translateY(1px)` and the edge shrinks to `1px`; disabled → `opacity: 0.4`.
- **Bet** (`.btn-bet`): same oxblood fill at `13px 20px`, `0 2px 0 rgba(0,0,0,0.3)` edge.
- **Ghost** (`.btn-ghost`): transparent, `1.5px` bone (or oxblood on paper) border, bone-2 text, `11px 20px`. Hover raises border and text to full bone / tints the paper.
- **Fold / Check-Call** (`.action-btn` variants): transparent with a `1.5px` border only — fold uses a faint bone border, check-call a bone-dim border. These stay quiet so bet reads as the loud option.
- **Focus:** `2.5px` bone outline, `3px` offset (`oxblood` on paper surfaces).

### Chips (table-size selector)
- **Style:** transparent stamp, `1.5px` `rule-strong` border, `2px` radius, Caslon Display `1.5rem` numeral over a Franklin uppercase sub-label.
- **State:** hover raises the border to oxblood; active fills solid oxblood with bone text. Selection is fill, not colour-shift alone.

### Cards / Containers (`.ledger-sheet`)
- **Corner Style:** `2px` (square on full-bleed game page and header bands).
- **Background:** bone paper (`#ece3cf`) with a `linear-gradient` margin rule at 44px and a `repeating-linear-gradient` horizontal ruling every 32px. `.no-hrule` keeps only the margin rule.
- **Shadow Strategy:** Sheet drop (see Elevation) on the baize ground; stripped entirely when the sheet is the full-bleed game page.
- **Border:** `1px` `paper-edge`, darker on the bottom edge.
- **Internal Padding:** `32px 30px 34px` desktop, `22px 16px 26px` on narrow screens.

### Playing Cards
- **Face:** warm bone (`#f7f0dd`), `54×76px` (`66×92` hero, `27×38` seat, `20×28` phone seat), `3px` radius, Caslon Display rank/suit, `1px` ink keyline plus a double inset keyline. Red suits use oxblood `#8a2b2b`, never pure red.
- **Back:** cross-hatched `repeating-linear-gradient` in oxblood-deep on bone.
- **Deal:** `dealIn` — a `0.3s` drop with a slight rotate, `both` fill.

### Inputs / Fields
No text inputs in the shipped surface. All selection is via stamps (table size) and ruled rows with a drawn-tick checkbox (roster). The checkbox is a `22px` `1.5px` ink-soft square that fills oxblood with a bone engraving-stroke tick when selected.

### Navigation
- **Style:** sticky top band, `#3d1c20` (oxblood-deep) fill, `1px` oxblood bottom border with an `inset 0 -3px 0 rgba(0,0,0,0.35)` drawn under-shadow.
- **Typography:** Caslon Display wordmark `clamp(1.3rem, 3vw, 1.7rem)` with an italic bone-dim ampersand and an inline club glyph; a Franklin tracked-caps tag ("THE CARD ROOM") that hides below 560px.
- No hover/active nav states — it is a masthead, not a menu.

### The Running-Account Spine (`.ledger-head`)
The persistent header of the game page: Caslon "The Card Room" title with a Franklin "Account of play" sub, right-aligned Your stack / This session figures (Caslon numerals, tabular, green up / oxblood down), and a hand-and-street line with a Franklin street track. Closed by a `3px double` ink-soft rule.

### The Engraved-Plate Table
`.table-rail` is the `#182a20` plate with the Plate cast shadow; `::after` draws the inner double keyline. `.table-felt` is the sunken field (radial baize-well gradient, inset well shadow, faint engraved house mark). Seats carry portrait medallion, name (Caslon, dark text-shadow for legibility on the field), stack, tendency gauge, bet chip and cards. Top-arc seats hide face-down backs and the tendency gauge; on phones the table goes portrait and seats regain both.

### The Tendency Gauge (`.seat-tendency`)
A `66×6px` inked track with a centre neutral tick and a `3×14px` bone mark showing this match's observed fold/aggression lean, with a Franklin word label below. `.is-unread` italicises the label to "reading…" until 8 decisions are seen. On phones the track shrinks to `44px` and the word label is hidden — the gauge stays visual.

### The Play Column + Margin Note (`.log-panel` / `.play-detail`)
Moves grouped by named street (`.pl-street`, Franklin tracked caps), each move a full-width row: Caslon name with an inline portrait mark, italic Caslon action, `1px` hairline divider. Post-hand a move with a read becomes a button (`.has-read`) with a dotted underline on the action; hover/focus tints it oxblood, pinned rows get an oxblood wash. The read fills the `.play-detail` panel below — a bone margin note under a `3px double` rule.

### Floating Taunt Scrap (`.speech-bubble`)
A bone paper scrap pinned over a seat with an oxblood pin dot and a paper tail, italic Caslon Text, rotated ~-1deg, `max-width: 176px`. `scrapIn` on entry, auto `scrapOut` at ~3.15s. `.is-loud` (bluff-win / bad-beat moments) goes larger, upright, bold, with a `3px` oxblood top rule and wider max-width.

### The Result Leaf (`.result-banner`)
Full-bleed, `paper-shade` fill between two `3px double` ink rules, Caslon headline + Franklin tabular sub. The one authored motion: `pageTurn` — `perspective(1400px) rotateY(-16deg)` settling to flat over `0.5s`. Under `prefers-reduced-motion` it becomes a `0.15s` fade.

### Portrait Medallions (`portraits.js`)
Seven authored inline-SVG bot marks plus a "you" empty-chair mark and game-over outcome marks. One engraving line, `stroke-width: 2.4`, `currentColor` ink so the same mark reads ink-on-paper in the roster and bone-on-baize at the table. Framed in a vertical ellipse with a double inner keyline (brass keyline in the roster, bone at the table).

## Do's and Don'ts

### Do:
- **Do** keep the ledger metaphor literal: ruled bone paper, a vertical oxblood margin rule ~44px in, `3px double` ink rules for section breaks.
- **Do** draw every "metal" element as `2.4`-stroke `currentColor` linework in the portrait hand.
- **Do** set voice in Caslon (names, headings, pot, italic taunts, action words) and figures/labels/state tags in Franklin tracked caps with `tabular-nums` on anything that changes.
- **Do** give every table state (turn, folded, all-in, street, button, SB/BB) a shape, label or drawn mark in addition to any colour.
- **Do** render ticks in the engraving stroke as SVG — never a Unicode glyph.
- **Do** reserve `#2f5233` and oxblood for money direction only.
- **Do** let the table be the one object with a real offset+blur cast shadow; keep everything else flat.
- **Do** update seats in place; never rebuild the table on a poll.
- **Do** cover `prefers-reduced-motion` for any new motion (the only sanctioned moment is the result-leaf `pageTurn`).

### Don't:
- **Don't** use gloss gradients, inset bevels, or any imitation brass/metal fill. Brass is the flat `#7d5f30` keyline only.
- **Don't** add glass, glow, gradient text, drop-shadow halos, or any zero-offset coloured shadow — least of all on the acting seat.
- **Don't** introduce a shadow as a hover or state cue; use outline, position, or label.
- **Don't** use pure red for card suits — oxblood `#8a2b2b`.
- **Don't** let colour be the only carrier of any state.
- **Don't** round corners past `3px` or soften the portrait/table ellipses into generic pills.
- **Don't** mix the type hands: no Franklin for voice, no Caslon for operational labels.
- **Don't** read as fintech or casino neon — the incumbent dark-navy / gold / cyan-pink-purple world is the rejected anti-reference.
- **Don't** add kickers, eyebrows, or standalone glyph icons; the club mark and portrait marks are the only iconography.
