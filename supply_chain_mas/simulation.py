"""Multi-period simulation of a three-tier supply chain.

Each period:

1. deliveries arrive, suppliers get fresh capacity, manufacturers produce;
2. manufacturers negotiate component purchases with the suppliers;
3. retailers negotiate product purchases with the manufacturers;
4. retailers serve stochastic customer demand;
5. holding costs are charged and metrics recorded.
"""

from __future__ import annotations

import csv
import random
from statistics import mean
from typing import Any, Dict, List, Optional

from .agents import Agent, ManufacturerAgent, RetailerAgent, SupplierAgent, TradingAgent
from .external import LegacyQuotationSystem, LegacySupplierAdapter
from .messaging import MessageBus
from .negotiation import STRATEGIES, make_strategy


class Simulation:
    def __init__(self, bus: MessageBus, suppliers: List[Agent],
                 manufacturers: List[ManufacturerAgent], retailers: List[RetailerAgent]) -> None:
        self.bus = bus
        self.suppliers, self.manufacturers, self.retailers = suppliers, manufacturers, retailers
        self.agents: List[Agent] = [*suppliers, *manufacturers, *retailers]
        self.history: List[Dict[str, Any]] = []
        self.period = 0

    @property
    def negotiations(self) -> List[Dict[str, Any]]:
        buyers = [a for a in self.agents if isinstance(a, TradingAgent)]
        return sorted((n for a in buyers for n in a.negotiation_log),
                      key=lambda n: n["conversation"])

    def step(self) -> Dict[str, Any]:
        self.period += 1
        t = self.period
        messages_before, deals_before = len(self.bus.log), len(self.negotiations)
        for agent in self.agents:
            agent.begin_period(t)
        # Buyers take turns in rotating order so nobody always gets first pick.
        for tier in (self.manufacturers, self.retailers):
            shift = t % len(tier)
            for buyer in tier[shift:] + tier[:shift]:
                buyer.plan_procurement()
                self.bus.run()
        demand = sold = 0
        for retailer in self.retailers:
            d, s = retailer.serve_customers()
            demand, sold = demand + d, sold + s
        for agent in self.agents:
            agent.end_period(t)

        new = self.negotiations[deals_before:]
        done = [n for n in new if n["success"]]

        def avg_price(item: str) -> Optional[float]:
            prices = [n["price"] for n in done if n["item"] == item]
            return round(mean(prices), 2) if prices else None

        record = {
            "period": t, "demand": demand, "sales": sold,
            "fill_rate": round(sold / demand, 3) if demand else 1.0,
            "negotiations": len(new), "agreements": len(done),
            "avg_rounds": round(mean(n["rounds"] for n in new), 2) if new else 0.0,
            "component_price": avg_price("component"), "product_price": avg_price("product"),
            "messages": len(self.bus.log) - messages_before,
            "chain_profit": round(sum(a.cash for a in self.agents), 2),
        }
        self.history.append(record)
        return record

    def run(self, periods: int) -> List[Dict[str, Any]]:
        for _ in range(periods):
            self.step()
        return self.history

    def summary(self) -> Dict[str, Any]:
        negotiations = self.negotiations
        done = [n for n in negotiations if n["success"]]
        demand = sum(r.demand_total for r in self.retailers)
        sales = sum(r.sales_total for r in self.retailers)
        return {
            "periods": self.period,
            "service_level": sales / demand if demand else 1.0,
            "agreement_rate": len(done) / len(negotiations) if negotiations else 0.0,
            "avg_rounds": mean(n["rounds"] for n in negotiations) if negotiations else 0.0,
            "messages": len(self.bus.log),
            "chain_profit": sum(a.cash for a in self.agents),
            "profit": {a.name: a.cash for a in self.agents},
        }

    def write_csv(self, path: str) -> None:
        with open(path, "w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(self.history[0]))
            writer.writeheader()
            writer.writerows(self.history)


def build_supply_chain(seed: int = 42, strategy: str = "mixed", include_legacy: bool = True,
                       deadline: int = 10) -> Simulation:
    """Default scenario: 3 suppliers (+1 external system), 2 manufacturers, 2 retailers.

    ``strategy`` is one of :data:`STRATEGIES` (every agent uses it) or
    ``"mixed"`` (agents use different strategies and deadlines).
    """
    rng = random.Random(seed)
    mixed = iter(STRATEGIES * 3)

    def kw(offset: int = 0) -> Dict[str, Any]:
        if strategy == "mixed":
            return {"strategy": make_strategy(next(mixed)), "deadline": deadline + offset}
        return {"strategy": make_strategy(strategy), "deadline": deadline}

    suppliers: List[Agent] = [
        SupplierAgent("Supplier-A", unit_cost=10.0, capacity=50, **kw()),
        SupplierAgent("Supplier-B", unit_cost=9.5, capacity=60, **kw(2)),
        SupplierAgent("Supplier-C", unit_cost=11.0, capacity=40, lead_times=(1, 3), **kw(-2)),
    ]
    if include_legacy:
        suppliers.append(LegacySupplierAdapter("Legacy-ERP", LegacyQuotationSystem()))
    manufacturers = [
        ManufacturerAgent("Maker-1", production_cost=5.0, capacity=60, **kw()),
        ManufacturerAgent("Maker-2", production_cost=5.5, capacity=50, **kw(2)),
    ]
    retailers = [
        RetailerAgent("Retail-North", mean_demand=42, demand_sd=8,
                      rng=random.Random(rng.random()), **kw()),
        RetailerAgent("Retail-South", mean_demand=36, demand_sd=10,
                      rng=random.Random(rng.random()), **kw(-2)),
    ]
    bus = MessageBus()
    simulation = Simulation(bus, suppliers, manufacturers, retailers)
    for agent in simulation.agents:
        bus.register(agent, agent.services)
    return simulation
