"""
Personality metadata for the playable bot roster: display name, avatar, tagline,
and situational taunts. Purely presentational -- none of this affects an agent's
actual decisions (those live in each agent's own act()/observe()); it's what the
web UI shows next to a bot's seat and in its chat bubble.

Each entry is keyed by a short slug used elsewhere (the web UI's opponent picker,
app.py's agent factory). `taunts` maps a trigger name to a list of lines; callers
pick one at random via get_taunt(). Triggers used by the UI:
  fold, check, call, bet_25, bet_50, bet_100, raise_25, raise_50, raise_100,
  all_in, win, lose, bad_beat, bluff_win, idle
Bet/raise triggers carry their pot-fraction size (see app.py's
_trigger_for_action) so a personality can have a different line for a small
feeler bet vs. a pot-sized one; get_taunt() falls back to the generic "bet"/
"raise" bucket if a personality has no line for that exact size.
"""

import random
from typing import Dict, List, Optional

PERSONALITIES: Dict[str, dict] = {
    "wildcard": {
        "name": "Wildcard",
        "avatar": "🃏",
        "agent_class": "RandomAgent",
        "tagline": "No plan. No fear. No idea what happens next.",
        "difficulty": "Easy",
        "taunts": {
            "fold": ["Nah, not feeling this one.", "Random said no.", "Next hand, next chaos."],
            "check": ["Passing the vibe check.", "I'll just look, thanks.", "Free card, sure, whatever."],
            "call": ["Eh, I'll see it.", "Curiosity called.", "In for a penny."],
            "bet_25": ["Sure, why not.", "Small chaos, still chaos."],
            "bet_50": ["This seemed like a fun number.", "Chaos demands a bet."],
            "bet_100": ["Might as well go big-ish.", "Full pot? Sure, that's a number too."],
            "raise_25": ["A little raise, why not.", "Nudging the chaos forward."],
            "raise_50": ["Raising because I can.", "Vibes says raise."],
            "raise_100": ["Big raise! No idea why.", "Let's really find out together."],
            "all_in": ["ALL IN! No regrets -- yet.", "Chaos goes all-in, apparently.", "Wildest number on the table. Sending it."],
            "win": ["Ha! Even I'm surprised.", "Chaos wins again!", "Called it. (I didn't.)"],
            "lose": ["Worth a shot.", "The dice giveth, the dice taketh.", "Onward to the next disaster."],
            "bad_beat": ["...well that's unfortunate.", "Statistically inevitable, honestly."],
            "bluff_win": ["Wait, that actually worked?!", "I have never had a plan and this proves it."],
            "idle": ["Cards are fun shapes.", "What does this button do?", "I regret nothing (yet)."],
        },
    },
    "the-rock": {
        "name": "The Rock",
        "avatar": "🪨",
        "agent_class": "TightAgent",
        "tagline": "Folds until it doesn't. Then it's already over.",
        "difficulty": "Easy",
        "taunts": {
            "fold": ["Not worth my chips.", "Patience is a strategy.", "I'll wait for a real hand."],
            "check": ["Nothing to see here.", "I'll take the free card.", "No reason to spend chips yet."],
            "call": ["Acceptable price to see more.", "I'll allow it.", "Cheap enough to continue."],
            "bet_25": ["A small poke. Still meant.", "Testing the water, carefully."],
            "bet_50": ["I only bet when I mean it.", "This is not a bluff."],
            "bet_100": ["Full value. No apologies.", "You've been warned."],
            "raise_25": ["A measured raise. Nothing reckless.", "Just enough to matter."],
            "raise_50": ["Premium only.", "This hand earned it."],
            "raise_100": ["This is as loud as I get.", "Rare, and deliberate."],
            "all_in": ["I don't do this lightly.", "Every chip, for a reason.", "This is the hand I waited for."],
            "win": ["As expected.", "Discipline pays.", "Predictable. Effective."],
            "lose": ["Even the rock cracks sometimes.", "Noted for next time.", "Still the right process."],
            "bad_beat": ["Unlucky. Doesn't change my approach."],
            "bluff_win": ["...that was actually a bluff. Don't get used to it."],
            "idle": ["Waiting for a real hand.", "Patience.", "I've folded worse for less."],
        },
    },
    "the-mathematician": {
        "name": "The Mathematician",
        "avatar": "🧮",
        "agent_class": "EVAgent",
        "tagline": "Every decision is just expected value with extra steps.",
        "difficulty": "Medium",
        "taunts": {
            "fold": ["Negative EV. Easy fold.", "The numbers don't lie.", "No edge here. Passing."],
            "check": ["Zero-cost information.", "No edge to bet here.", "Free to continue, so I will."],
            "call": ["Pot odds justify it.", "The math says call.", "Correct price, so I'm in."],
            "bet_25": ["Small, cheap value.", "A thin edge, still worth taking."],
            "bet_50": ["Positive EV. Simple as that.", "The math checks out."],
            "bet_100": ["This is +EV by a comfortable margin.", "Maximum value, mathematically."],
            "raise_25": ["A small correction to the price.", "The odds shifted. Raising slightly."],
            "raise_50": ["Correct play, mathematically.", "Raising per the numbers."],
            "raise_100": ["The edge is significant here.", "This is not a small edge. Raising big."],
            "all_in": ["The equity supports this fully.", "Expected value approves of everything.", "This is the shove the math demands."],
            "win": ["Variance aligned with expectation.", "Over a large enough sample, this was inevitable.", "The model performed as designed."],
            "lose": ["Correct decisions can still lose. That's variance.", "I'd make the same play again.", "Losing this doesn't make it wrong."],
            "bad_beat": ["Low-probability outcome. Still just variance.", "The equity was there. The river wasn't."],
            "bluff_win": ["I don't bluff. That was a value bet you misread."],
            "idle": ["Calculating...", "Assuming a uniform opponent range...", "Running the numbers."],
        },
    },
    "the-profiler": {
        "name": "The Profiler",
        "avatar": "🕵️",
        "agent_class": "BayesianAgent",
        "tagline": "Learning how you play, one hand at a time. It gets worse for you.",
        "difficulty": "Hard",
        "taunts": {
            "fold": ["Not falling for that again.", "You bet big with air last time. Not buying it.", "I've seen where this goes."],
            "check": ["Let's see what you do with the initiative.", "I'll let you talk.", "Silence gathers information too."],
            "call": ["I don't think you have it.", "Your range is showing.", "This looks like a bluff to me."],
            "bet_25": ["A small probe, to see how you react.", "Testing a read here."],
            "bet_50": ["I've seen this pattern before.", "You do this with strong hands. I noticed."],
            "bet_100": ["This is exactly the spot I've been waiting for.", "Your tendencies built this bet."],
            "raise_25": ["A small adjustment to your line.", "Nudging based on what I know."],
            "raise_50": ["You don't fold to this size. I remember.", "Adjusting to you."],
            "raise_100": ["Every hand you've played led to this raise.", "Your history wrote this bet for me."],
            "all_in": ["I've profiled this exact spot for hands now.", "This is the read I've been building toward.", "Everything you've shown me says: shove."],
            "win": ["Your tells are getting easier to read.", "I've been watching you the whole session.", "The model of you just paid off."],
            "lose": ["Updating my model of you now.", "Noted. Recalibrating.", "Even a good read loses sometimes."],
            "bad_beat": ["Correct read, wrong river. It happens.", "My model had that at 80%+. Poker's cruel sometimes."],
            "bluff_win": ["You didn't call because I've trained you not to.", "That's what the last twenty hands were for."],
            "idle": ["Still watching.", "Every action is data.", "I know more about your game than you think."],
        },
    },
    "the-maniac": {
        "name": "The Maniac",
        "avatar": "🔥",
        "agent_class": "ManiacAgent",
        "tagline": "Fold equity is a myth if you never fold. Neither will it.",
        "difficulty": "Hard",
        "taunts": {
            "fold": ["...fine. ONE fold.", "Even I have limits. Rarely.", "Okay, that one wasn't worth it. Barely."],
            "check": ["Boring. I'll allow it once.", "Free card, then chaos resumes.", "Fine. For now."],
            "call": ["I'm not folding THIS.", "Never met a hand I didn't like.", "Calling. Obviously."],
            "bet_25": ["A small taste of chaos.", "Just warming up."],
            "bet_50": ["Bet. Always bet.", "Fortune favors the unhinged."],
            "bet_100": ["ALL IN energy, every hand.", "Full send. Why wouldn't I."],
            "raise_25": ["A tiny raise, for now.", "Just poking first."],
            "raise_50": ["Raise again? Raise again.", "You blinked. Raising."],
            "raise_100": ["Bigger raise. Obviously.", "You should've folded already."],
            "all_in": ["EVERYTHING. Every single time.", "This is the only setting I have.", "Fortune favors the reckless!"],
            "win": ["TOLD YOU.", "Fortune favors the reckless!", "That's what happens."],
            "lose": ["Worth it. Next hand, same plan.", "No regrets. Rebuying mentally.", "Chaos doesn't apologize."],
            "bad_beat": ["Doesn't matter. Firing again next hand.", "Cost of doing business."],
            "bluff_win": ["You folded the better hand. Every time. FOREVER."],
            "idle": ["I could bet right now.", "Why check when you can bet?", "Patience is for other people."],
        },
    },
    "calling-station": {
        "name": "Calling Station",
        "avatar": "📞",
        "agent_class": "CallingStationAgent",
        "tagline": "Will see literally one more card, thank you.",
        "difficulty": "Medium",
        "taunts": {
            "fold": ["Okay THAT I'm not paying for.", "Even I have a line. Somewhere.", "That's a bit much, even for me."],
            "check": ["I'll just look, thanks.", "Free is my favorite price.", "Checking, obviously."],
            "call": ["I'll see it.", "One more card never hurt anybody.", "Calling, obviously."],
            "bet_25": ["Might as well bet this small one.", "Rare bet from me. Cheap, though."],
            "bet_50": ["Feeling generous.", "Betting? Me? Sure, why not."],
            "bet_100": ["Big bet, from ME. Don't get used to it.", "Okay, I'm actually betting big."],
            "raise_25": ["A tiny raise. Historic, honestly.", "Look at me, raising a little."],
            "raise_50": ["Ooh, rare raise from me.", "This almost never happens."],
            "raise_100": ["A BIG raise?! From the calling station?!", "Mark this day down."],
            "all_in": ["...okay, this is new for me.", "Well, that's a first.", "I guess I'm all-in now. Wow."],
            "win": ["See? Calling works!", "Patience and curiosity, baby.", "Told you seeing cards pays off."],
            "lose": ["Worth it for the suspense.", "I'll call again next time too.", "Can't win 'em all, but I saw everything."],
            "bad_beat": ["Well, I called with less. Can't complain much."],
            "bluff_win": ["Wait, you were bluffing? I just wanted to see the cards."],
            "idle": ["I wonder what everyone has.", "I just like seeing flops.", "One more card, always."],
        },
    },
    "the-data-scientist": {
        "name": "The Data Scientist",
        "avatar": "🤖",
        "agent_class": "DataScientistAgent",
        "tagline": "Trained on thousands of simulated hands. Still learning.",
        "difficulty": "Hard",
        "taunts": {
            "fold": ["Low predicted value. Folding per the model.", "The blended estimate says get out.", "Both sub-models agree: fold."],
            "check": ["No signal strong enough to act on.", "Blended EV favors free information.", "Neither model likes betting here."],
            "call": ["Predicted action value favors calling here.", "The ensemble agrees: call.", "Weighted estimate points to calling."],
            "bet_25": ["Small edge, modest bet size.", "The model likes a light bet here."],
            "bet_50": ["Model confidence: high.", "The training data agrees with this bet."],
            "bet_100": ["High-confidence bet, full size.", "Both models converge on a big bet."],
            "raise_25": ["A small correction from the ensemble.", "Slight edge detected. Raising a little."],
            "raise_50": ["Feature importance says: raise.", "The blend favors raising here."],
            "raise_100": ["Strong signal from both sub-models. Raising big.", "High-confidence raise, ensemble-approved."],
            "all_in": ["Both models are converged and confident. Shoving.", "This is as high-confidence as the ensemble gets.", "Maximum predicted value. Going all-in."],
            "win": ["Validation set says this was the right call.", "Another data point in my favor.", "Model confidence, vindicated."],
            "lose": ["Logging this one for the next training run.", "Model's never perfect. Iterating.", "Adding this to the residuals."],
            "bad_beat": ["Out-of-distribution result. Noted for retraining."],
            "bluff_win": ["The model found an edge you didn't expect."],
            "idle": ["Running inference...", "Querying the deployment...", "Still generalizing well, I think."],
        },
    },
}


def get_taunt(personality_key: str, trigger: str, rng: Optional[random.Random] = None) -> str:
    """Return one random taunt line for this personality/trigger, or "" if
    unknown. A sized bet/raise trigger (bet_25, raise_100, ...) with no
    lines of its own falls back to the generic "bet"/"raise" bucket, so a
    personality still has *something* to say even for a size it doesn't
    single out."""
    entry = PERSONALITIES.get(personality_key)
    if not entry:
        return ""
    taunts = entry.get("taunts", {})
    lines: List[str] = taunts.get(trigger, [])
    if not lines and "_" in trigger:
        prefix = trigger.rsplit("_", 1)[0]
        if prefix in ("bet", "raise"):
            lines = taunts.get(prefix, [])
    if not lines:
        return ""
    r = rng or random
    return r.choice(lines)


def list_personalities() -> List[dict]:
    """Return the roster as a list of {key, name, avatar, tagline, difficulty} for
    the web UI's opponent picker, in a fixed display order."""
    order = [
        "wildcard", "calling-station", "the-rock",
        "the-mathematician", "the-maniac", "the-profiler", "the-data-scientist",
    ]
    out = []
    for key in order:
        entry = PERSONALITIES.get(key)
        if not entry:
            continue
        out.append({
            "key": key,
            "name": entry["name"],
            "avatar": entry["avatar"],
            "tagline": entry["tagline"],
            "difficulty": entry["difficulty"],
        })
    return out
