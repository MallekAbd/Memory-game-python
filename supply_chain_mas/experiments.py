"""Research experiments on negotiation strategies.

1. :func:`strategy_tournament` - every buyer strategy against every seller
   strategy on randomly generated bilateral negotiations.
2. :func:`chain_comparison` - the full supply chain with all agents using the
   same strategy, to see how negotiation behaviour affects chain performance.
"""

from __future__ import annotations

import random
from statistics import mean
from typing import Any, Dict, List

from .negotiation import STRATEGIES, Negotiator, Preferences, make_strategy, run_bilateral
from .simulation import build_supply_chain


def strategy_tournament(trials: int = 500, seed: int = 1) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    scenarios = []
    for _ in range(trials):
        seller_reserve = rng.uniform(8, 14)
        buyer_reserve = rng.uniform(10, 18)
        scenarios.append((
            Preferences(0.6 * buyer_reserve, buyer_reserve, 1, 4, w_price=rng.uniform(0.4, 0.8)),
            Preferences(1.6 * seller_reserve, seller_reserve, 4, 1, w_price=rng.uniform(0.6, 0.9)),
            rng.randint(6, 14), rng.randint(6, 14)))
    rows = []
    for buyer_name in STRATEGIES:
        for seller_name in STRATEGIES:
            outcomes = [run_bilateral(
                Negotiator(bp, make_strategy(buyer_name), bd, 100),
                Negotiator(sp, make_strategy(seller_name), sd, 100), 100)
                for bp, sp, bd, sd in scenarios]
            deals = [o for o in outcomes if o.agreed]
            rows.append({
                "buyer": buyer_name, "seller": seller_name,
                "agreement_rate": len(deals) / trials,
                "buyer_utility": mean(o.buyer_utility for o in outcomes),
                "seller_utility": mean(o.seller_utility for o in outcomes),
                "joint_utility": mean(o.buyer_utility + o.seller_utility for o in outcomes),
                "rounds": mean(o.rounds for o in deals) if deals else 0.0,
            })
    return rows


def chain_comparison(periods: int = 30, seeds: int = 5) -> List[Dict[str, Any]]:
    rows = []
    for name in (*STRATEGIES, "mixed"):
        runs = []
        for seed in range(seeds):
            simulation = build_supply_chain(seed=seed, strategy=name)
            simulation.run(periods)
            runs.append(simulation.summary())
        rows.append({
            "strategy": name,
            "service_level": mean(r["service_level"] for r in runs),
            "agreement_rate": mean(r["agreement_rate"] for r in runs),
            "avg_rounds": mean(r["avg_rounds"] for r in runs),
            "messages": mean(r["messages"] for r in runs),
            "chain_profit": mean(r["chain_profit"] for r in runs),
        })
    return rows


def format_table(rows: List[Dict[str, Any]]) -> str:
    def cell(value: Any) -> str:
        if value is None:
            return "-"
        return f"{value:.3f}" if isinstance(value, float) else str(value)

    headers = list(rows[0])
    table = [headers] + [[cell(row[h]) for h in headers] for row in rows]
    widths = [max(len(line[i]) for line in table) for i in range(len(headers))]
    lines = ["  ".join(c.ljust(w) for c, w in zip(line, widths)) for line in table]
    lines.insert(1, "  ".join("-" * w for w in widths))
    return "\n".join(lines)
