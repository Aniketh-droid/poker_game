import random
import unittest

from agents.personalities import PERSONALITIES, get_taunt

_CORE_TRIGGERS = ["fold", "check", "call", "win", "lose", "idle"]
_SIZED_TRIGGERS = ["bet_25", "bet_50", "bet_100", "raise_25", "raise_50", "raise_100", "all_in"]


class TestPersonalityTaunts(unittest.TestCase):
    def test_every_personality_has_every_core_and_sized_trigger(self):
        for key, entry in PERSONALITIES.items():
            taunts = entry["taunts"]
            for trig in _CORE_TRIGGERS + _SIZED_TRIGGERS:
                with self.subTest(personality=key, trigger=trig):
                    self.assertTrue(taunts.get(trig), f"{key} missing lines for {trig}")

    def test_get_taunt_is_deterministic_with_a_seeded_rng(self):
        line1 = get_taunt("the-maniac", "all_in", rng=random.Random(5))
        line2 = get_taunt("the-maniac", "all_in", rng=random.Random(5))
        self.assertEqual(line1, line2)

    def test_unknown_sized_trigger_with_no_generic_bucket_returns_empty(self):
        self.assertEqual(get_taunt("the-rock", "bet_37", rng=random.Random(0)), "")

    def test_unknown_personality_or_trigger_returns_empty(self):
        self.assertEqual(get_taunt("not-a-real-bot", "fold"), "")
        self.assertEqual(get_taunt("the-rock", "not-a-real-trigger"), "")


if __name__ == "__main__":
    unittest.main()
