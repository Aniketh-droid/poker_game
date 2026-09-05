"""
Personality metadata for the playable bot roster: display name, avatar, tagline,
and situational taunts. Purely presentational -- none of this affects an agent's
actual decisions (those live in each agent's own act()/observe()); it's what the
web UI shows next to a bot's seat and in its chat bubble.

Each entry is keyed by a short slug used elsewhere (the web UI's opponent picker,
app.py's agent factory). `taunts` maps a trigger name to a list of lines; callers
pick one at random via get_taunt(). Triggers used by the UI:
  bet, raise, call, fold, check, win, lose, bad_beat, bluff_win, idle
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
            "bet": ["Sure, why not.", "This seemed like a fun number.", "Chaos demands a bet."],
            "raise": ["Let's find out together!", "Raising because I can.", "Vibes says raise."],
            "call": ["Eh, I'll see it.", "Curiosity called.", "In for a penny."],
            "fold": ["Nah, not feeling this one.", "Random said no.", "Next hand, next chaos."],
            "check": ["Passing the vibe check.", "I'll just look, thanks."],
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
            "bet": ["I only bet when I mean it.", "This is not a bluff.", "You've been warned."],
            "raise": ["Premium only.", "This hand earned it."],
            "call": ["Acceptable price to see more.", "I'll allow it."],
            "fold": ["Not worth my chips.", "Patience is a strategy.", "I'll wait for a real hand."],
            "check": ["Nothing to see here.", "I'll take the free card."],
            "win": ["As expected.", "Discipline pays.", "Predictable. Effective."],
            "lose": ["Even the rock cracks sometimes.", "Noted for next time."],
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
            "bet": ["Positive EV. Simple as that.", "The math checks out.", "This is +EV by a comfortable margin."],
            "raise": ["Correct play, mathematically.", "Raising per the numbers."],
            "call": ["Pot odds justify it.", "The math says call."],
            "fold": ["Negative EV. Easy fold.", "The numbers don't lie."],
            "check": ["Zero-cost information.", "No edge to bet here."],
            "win": ["Variance aligned with expectation.", "Over a large enough sample, this was inevitable."],
            "lose": ["Correct decisions can still lose. That's variance.", "I'd make the same play again."],
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
            "bet": ["I've seen this pattern before.", "You do this with strong hands. I noticed.", "Adjusting to you."],
            "raise": ["You don't fold to this size. I remember.", "This is exactly the spot I've been waiting for."],
            "call": ["I don't think you have it.", "Your range is showing."],
            "fold": ["Not falling for that again.", "You bet big with air last time. Not buying it now... wait, you don't. Fine."],
            "check": ["Let's see what you do with the initiative.", "I'll let you talk."],
            "win": ["Your tells are getting easier to read.", "I've been watching you the whole session."],
            "lose": ["Updating my model of you now.", "Noted. Recalibrating."],
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
            "bet": ["ALL IN energy, every hand.", "Bet. Always bet.", "Fortune favors the unhinged."],
            "raise": ["Raise again? Raise again.", "You blinked. Raising."],
            "call": ["I'm not folding THIS.", "Never met a hand I didn't like."],
            "fold": ["...fine. ONE fold.", "Even I have limits. Rarely."],
            "check": ["Boring. I'll allow it once.", "Free card, then chaos resumes."],
            "win": ["TOLD YOU.", "Fortune favors the reckless!", "That's what happens."],
            "lose": ["Worth it. Next hand, same plan.", "No regrets. Rebuying mentally."],
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
            "bet": ["Might as well bet this one.", "Feeling generous."],
            "raise": ["Ooh, rare raise from me."],
            "call": ["I'll see it.", "One more card never hurt anybody.", "Calling, obviously."],
            "fold": ["Okay THAT I'm not paying for.", "Even I have a line. Somewhere."],
            "check": ["I'll just look, thanks.", "Free is my favorite price."],
            "win": ["See? Calling works!", "Patience and curiosity, baby."],
            "lose": ["Worth it for the suspense.", "I'll call again next time too."],
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
            "bet": ["Model confidence: high.", "The training data agrees with this bet."],
            "raise": ["Feature importance says: raise."],
            "call": ["Predicted action value favors calling here."],
            "fold": ["Low predicted value. Folding per the model."],
            "check": ["No signal strong enough to act on."],
            "win": ["Validation set says this was the right call.", "Another data point in my favor."],
            "lose": ["Logging this one for the next training run.", "Model's never perfect. Iterating."],
            "bad_beat": ["Out-of-distribution result. Noted for retraining."],
            "bluff_win": ["The model found an edge you didn't expect."],
            "idle": ["Running inference...", "Querying the deployment...", "Still generalizing well, I think."],
        },
    },
}


def get_taunt(personality_key: str, trigger: str, rng: Optional[random.Random] = None) -> str:
    """Return one random taunt line for this personality/trigger, or "" if unknown."""
    entry = PERSONALITIES.get(personality_key)
    if not entry:
        return ""
    lines: List[str] = entry.get("taunts", {}).get(trigger, [])
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
