"""
Run multi-seed experiments and print statistically meaningful summaries.
"""

import time
from evaluation.hand_evaluator import compare as compare_hands


class EvalWrapper:
    @staticmethod
    def compare(hand1, hand2):
        return compare_hands(hand1, hand2)


def _entropy_summary(entropy_history):
    if not entropy_history:
        return {"samples": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "last": 0.0}
    return {
        "samples": len(entropy_history),
        "mean": sum(entropy_history) / len(entropy_history),
        "min": min(entropy_history),
        "max": max(entropy_history),
        "last": entropy_history[-1],
    }


def _run_pairing(name, agent1_factory, agent2_factory, hands, seeds, samples):
    from experiments.match_runner import run_match
    from experiments.statistics import report, summarize_runs

    evaluator = EvalWrapper()
    run_means = []
    run_win_rates = []
    run_tie_rates = []
    run_bluff_failure = []
    final_result = None
    all_chip_deltas = []
    all_entropy = []
    start = time.time()

    print(f"\n=== {name} ===")
    print(f"Config: hands={hands}, samples={samples}, seeds={len(seeds)}")
    for idx, seed in enumerate(seeds):
        agent1 = agent1_factory(seed)
        agent2 = agent2_factory(seed + 10000)
        result = run_match(
            agent1,
            agent2,
            hands=hands,
            seed=seed,
            evaluator=evaluator,
            progress_interval=max(1, hands // 5),
        )
        stats = report(result["chip_deltas"])
        run_means.append(stats["mean"])
        run_win_rates.append(result["win_rate_agent1"])
        run_tie_rates.append(result["tie_rate"])
        run_bluff_failure.append(result.get("bluff_failure_rate_agent1", 0.0))
        final_result = result
        all_chip_deltas.extend(result["chip_deltas"])
        all_entropy.extend(result.get("entropy_history", []))
        print(
            f"Seed {idx + 1}/{len(seeds)} ({seed}) -> "
            f"win={result['win_rate_agent1']:.2%}, tie={result['tie_rate']:.2%}, "
            f"mean_chip={stats['mean']:.4f}"
        )

    mean_summary = summarize_runs(run_means)
    win_summary = summarize_runs(run_win_rates)
    tie_summary = summarize_runs(run_tie_rates)
    bluff_summary = summarize_runs(run_bluff_failure)
    elapsed = time.time() - start

    print("--- Aggregate across seeds (agent1 perspective) ---")
    print(
        f"Mean chip gain: {mean_summary['mean']:.4f} "
        f"(95% CI [{mean_summary['ci95_low']:.4f}, {mean_summary['ci95_high']:.4f}])"
    )
    print(
        f"Win rate: {win_summary['mean']:.2%} "
        f"(95% CI [{win_summary['ci95_low']:.2%}, {win_summary['ci95_high']:.2%}])"
    )
    print(
        f"Tie rate: {tie_summary['mean']:.2%} "
        f"(95% CI [{tie_summary['ci95_low']:.2%}, {tie_summary['ci95_high']:.2%}])"
    )
    print(
        f"Bluff failure rate: {bluff_summary['mean']:.2%} "
        f"(95% CI [{bluff_summary['ci95_low']:.2%}, {bluff_summary['ci95_high']:.2%}])"
    )
    print(f"Elapsed: {elapsed:.1f}s")

    if final_result is not None and "entropy_history" in final_result:
        es = _entropy_summary(final_result["entropy_history"])
        if es["samples"] > 0:
            print("--- Entropy (last run, agent1 if Bayesian) ---")
            print(
                f"samples={es['samples']} mean={es['mean']:.4f} "
                f"min={es['min']:.4f} max={es['max']:.4f} last={es['last']:.4f}"
            )

    try:
        from experiments.visualize import plot_match_stats
        save_path = f"plots/{name.replace(' ', '_').lower()}.png"
        
        # Calculate raw counts for the pie chart
        total_hands = hands * len(seeds)
        wins1 = win_summary['mean'] * total_hands
        ties_count = tie_summary['mean'] * total_hands
        wins2 = total_hands - wins1 - ties_count

        plot_match_stats(all_chip_deltas, all_entropy, name, name.split(' vs ')[0], name.split(' vs ')[1], save_path=f"static/{save_path}", wins1=wins1, wins2=wins2, ties=ties_count)
    except Exception as e:
        print(f"Could not generate plot for {name}: {e}")
        save_path = None

    return {
        "name": name,
        "mean_chip_gain": mean_summary['mean'],
        "win_rate": win_summary['mean'],
        "tie_rate": tie_summary['mean'],
        "elapsed": elapsed,
        "plot_path": save_path
    }


def main() -> None:
    from agents.bayesian_agent import BayesianAgent
    from agents.ev_agent import EVAgent
    from agents.random_agent import RandomAgent

    hands = 500
    samples = 25
    seeds = [12345, 23456, 34567]

    _run_pairing(
        "Bayesian vs EV",
        lambda s: BayesianAgent(player_id=0, epsilon=0.05, samples=samples, seed=s, opponent_type="TIGHT", forgetting_factor=0.01),
        lambda s: EVAgent(player_id=1, epsilon=0.05, samples=samples, seed=s),
        hands=hands,
        seeds=seeds,
        samples=samples,
    )
    _run_pairing(
        "Bayesian vs Random",
        lambda s: BayesianAgent(player_id=0, epsilon=0.05, samples=samples, seed=s, opponent_type="LOOSE", forgetting_factor=0.01),
        lambda s: RandomAgent(player_id=1),
        hands=hands,
        seeds=seeds,
        samples=samples,
    )
    _run_pairing(
        "EV vs Random",
        lambda s: EVAgent(player_id=0, epsilon=0.05, samples=samples, seed=s),
        lambda s: RandomAgent(player_id=1),
        hands=hands,
        seeds=seeds,
        samples=samples,
    )


if __name__ == "__main__":
    main()
