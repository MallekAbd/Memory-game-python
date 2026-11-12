import unittest

from supply_chain_mas.agents import ManufacturerAgent, SupplierAgent
from supply_chain_mas.external import LegacyQuotationSystem, LegacySupplierAdapter
from supply_chain_mas.messaging import Message, MessageBus, Performative
from supply_chain_mas.negotiation import (STRATEGIES, Negotiator, Offer, Preferences,
                                          make_strategy, run_bilateral)
from supply_chain_mas.simulation import build_supply_chain

BUYER = Preferences(9.0, 15.0, delivery_best=1, delivery_worst=4, w_price=0.6)
SELLER = Preferences(16.0, 10.5, delivery_best=4, delivery_worst=1, w_price=0.8)


class NegotiationTests(unittest.TestCase):
    def test_utility_endpoints(self):
        self.assertAlmostEqual(BUYER.utility(Offer(9.0, 1, 10)), 1.0)
        self.assertAlmostEqual(BUYER.utility(Offer(15.0, 4, 10)), 0.0)
        self.assertLess(BUYER.utility(Offer(16.0, 4, 10)), 0.0)
        self.assertAlmostEqual(SELLER.utility(Offer(16.0, 4, 10)), 1.0)

    def test_make_offer_hits_target_and_respects_reservation(self):
        for prefs in (BUYER, SELLER):
            for target in (0.0, 0.2, 0.5, 0.8, 1.0):
                offer = prefs.make_offer(target, 10, toward=Offer(12.0, 2, 10))
                self.assertGreaterEqual(prefs.utility(offer), target - 1e-2)
                self.assertGreaterEqual(prefs.utility(offer), 0.0)

    def test_time_dependent_strategies_concede_monotonically(self):
        for name in ("boulware", "linear", "conceder"):
            strategy = make_strategy(name)
            targets = [strategy.target(t / 10, None) for t in range(11)]
            self.assertEqual(targets, sorted(targets, reverse=True))
            self.assertAlmostEqual(targets[0], 1.0)
        self.assertGreater(make_strategy("boulware").target(0.5, None),
                           make_strategy("conceder").target(0.5, None))

    def test_bilateral_deal_is_individually_rational(self):
        for buyer_s in STRATEGIES:
            for seller_s in STRATEGIES:
                outcome = run_bilateral(Negotiator(BUYER, make_strategy(buyer_s), 10, 50),
                                        Negotiator(SELLER, make_strategy(seller_s), 10, 50), 50)
                if outcome.agreed:
                    self.assertGreaterEqual(outcome.buyer_utility, 0.0)
                    self.assertGreaterEqual(outcome.seller_utility, 0.0)
        linear = make_strategy("linear")
        self.assertTrue(run_bilateral(Negotiator(BUYER, linear, 10, 50),
                                      Negotiator(SELLER, linear, 10, 50), 50).agreed)

    def test_no_deal_without_zone_of_agreement(self):
        greedy = Preferences(30.0, 20.0, delivery_best=4, delivery_worst=1, w_price=0.8)
        linear = make_strategy("linear")
        outcome = run_bilateral(Negotiator(BUYER, linear, 10, 50),
                                Negotiator(greedy, linear, 10, 50), 50)
        self.assertFalse(outcome.agreed)


class MessagingTests(unittest.TestCase):
    def test_json_round_trip(self):
        message = Message("a", "b", Performative.PROPOSE, "c1", {"price": 1.5, "round": 2})
        self.assertEqual(Message.from_json(message.to_json()), message)

    def test_unknown_receiver_rejected(self):
        with self.assertRaises(KeyError):
            MessageBus().send(Message("a", "nobody", Performative.CFP, "c1"))


class AgentTests(unittest.TestCase):
    def _market(self, *sellers):
        bus = MessageBus()
        buyer = ManufacturerAgent("maker", components=0)
        for agent in (buyer, *sellers):
            bus.register(agent, agent.services)
            agent.begin_period(1)
        return bus, buyer

    def test_order_is_split_across_suppliers(self):
        s1 = SupplierAgent("s1", unit_cost=10, capacity=40)
        s2 = SupplierAgent("s2", unit_cost=10, capacity=40)
        bus, buyer = self._market(s1, s2)
        buyer.procure("component", 70)
        bus.run()
        deal = buyer.negotiation_log[-1]
        self.assertTrue(deal["success"])
        self.assertEqual(deal["quantity"], 70)
        self.assertEqual(s1.units_sold + s2.units_sold, 70)
        self.assertEqual(buyer.inbound.on_order, 70)
        self.assertLessEqual(deal["price"], buyer.max_component_price)
        self.assertGreaterEqual(deal["price"], 10 * 1.05)
        # money is conserved between buyer and sellers (sellers also pay unit cost)
        self.assertAlmostEqual(-buyer.cash, s1.cash + s2.cash + 70 * 10, places=6)

    def test_native_buyer_trades_with_external_system(self):
        legacy = LegacySupplierAdapter("legacy", LegacyQuotationSystem(weekly_capacity=30))
        bus, buyer = self._market(legacy)
        buyer.procure("component", 50)
        bus.run()
        deal = buyer.negotiation_log[-1]
        self.assertTrue(deal["success"])
        self.assertEqual(deal["quantity"], 30)          # limited by the legacy capacity
        self.assertGreaterEqual(deal["price"], legacy.system.floor_price)
        self.assertEqual(legacy.system.free_capacity, 0)


class SimulationTests(unittest.TestCase):
    def test_full_chain_runs_and_stays_consistent(self):
        for strategy in (*STRATEGIES, "mixed"):
            simulation = build_supply_chain(seed=3, strategy=strategy)
            simulation.run(15)
            summary = simulation.summary()
            self.assertGreater(summary["agreement_rate"], 0.5)
            self.assertGreater(summary["service_level"], 0.5)
            for maker in simulation.manufacturers:
                self.assertGreaterEqual(maker.products, 0)
                self.assertGreaterEqual(maker.components, 0)
            for supplier in simulation.suppliers[:3]:
                self.assertGreaterEqual(supplier.capacity_left, 0)
                self.assertGreaterEqual(supplier.cash, 0.0)  # never sells below cost

    def test_reproducible(self):
        a = build_supply_chain(seed=7).run(8)
        b = build_supply_chain(seed=7).run(8)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
