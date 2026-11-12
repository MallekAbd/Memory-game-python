"""Command line interface: ``python -m supply_chain_mas [simulate|experiment]``."""

from __future__ import annotations

import argparse

from .experiments import chain_comparison, format_table, strategy_tournament
from .negotiation import STRATEGIES
from .simulation import build_supply_chain


def simulate(args: argparse.Namespace) -> None:
    simulation = build_supply_chain(seed=args.seed, strategy=args.strategy,
                                    include_legacy=not args.no_legacy, deadline=args.deadline)
    simulation.run(args.periods)

    if args.trace:
        first = simulation.bus.log[0].conversation_id
        print(f"=== Message trace of negotiation {first} ===")
        for message in simulation.bus.log:
            if message.conversation_id == first:
                print(message)
        print()

    print("=== Per-period results ===")
    print(format_table(simulation.history))

    print("\n=== Contracts of the last period ===")
    last = [n for n in simulation.negotiations if n["period"] == simulation.period]
    print(format_table([{k: n[k] for k in ("buyer", "item", "requested", "sellers", "price",
                                            "delivery", "quantity", "rounds")} for n in last]))

    summary = simulation.summary()
    print("\n=== Summary ===")
    print(f"service level (customer fill rate): {summary['service_level']:.1%}")
    print(f"negotiation agreement rate        : {summary['agreement_rate']:.1%}")
    print(f"average rounds per negotiation    : {summary['avg_rounds']:.2f}")
    print(f"messages exchanged                : {summary['messages']}")
    print(f"total supply-chain profit         : {summary['chain_profit']:.2f}")
    print("\nProfit per agent")
    for name, profit in summary["profit"].items():
        print(f"  {name:<14} {profit:>12.2f}")

    if args.csv:
        simulation.write_csv(args.csv)
        print(f"\nPer-period results written to {args.csv}")


def experiment(args: argparse.Namespace) -> None:
    print(f"=== Strategy tournament: {args.trials} random bilateral negotiations per pairing ===")
    print(format_table(strategy_tournament(trials=args.trials, seed=args.seed)))
    print(f"\n=== Whole-chain comparison: {args.periods} periods, "
          f"mean of {args.seeds} seeds ===")
    print(format_table(chain_comparison(periods=args.periods, seeds=args.seeds)))


def main() -> None:
    parser = argparse.ArgumentParser(prog="supply_chain_mas", description=__doc__)
    sub = parser.add_subparsers(dest="command")

    sim = sub.add_parser("simulate", help="run the supply-chain simulation (default)")
    exp = sub.add_parser("experiment", help="compare negotiation strategies")
    for p in (parser, sim):
        p.add_argument("--periods", type=int, default=20)
        p.add_argument("--seed", type=int, default=42)
        p.add_argument("--strategy", choices=(*STRATEGIES, "mixed"), default="mixed")
        p.add_argument("--deadline", type=int, default=10, help="negotiation deadline in rounds")
        p.add_argument("--no-legacy", action="store_true",
                       help="leave the external (adapter-linked) supplier out")
        p.add_argument("--trace", action="store_true", help="print one negotiation's messages")
        p.add_argument("--csv", help="write per-period results to this CSV file")
    exp.add_argument("--trials", type=int, default=500)
    exp.add_argument("--periods", type=int, default=30)
    exp.add_argument("--seeds", type=int, default=5)
    exp.add_argument("--seed", type=int, default=1)

    args = parser.parse_args()
    (experiment if args.command == "experiment" else simulate)(args)


if __name__ == "__main__":
    main()
