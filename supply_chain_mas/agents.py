"""Supply-chain agents.

:class:`TradingAgent` implements both sides of the negotiation protocol on top
of the message bus:

* as a **buyer** it runs a one-to-many negotiation - a call for proposals to
  every seller found in the directory, then concurrent alternating-offers
  threads; it signs the best acceptable offers and, when one seller cannot
  cover the whole order, splits it and keeps negotiating for the rest;
* as a **seller** it answers each buyer in an independent thread.

:class:`SupplierAgent`, :class:`ManufacturerAgent` and :class:`RetailerAgent`
add the business logic of each tier (capacity, production, inventory policy,
customer demand) and derive their negotiation preferences from it.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .messaging import Message, MessageBus, Performative
from .negotiation import ACCEPT, PROPOSE, Negotiator, Offer, Preferences, Strategy, make_strategy

COMPONENT, PRODUCT = "component", "product"
MAX_LEAD_TIME = 4  # periods


class Agent:
    """Minimal agent: a name, a mailbox handler and life-cycle hooks."""

    services: Tuple[str, ...] = ()

    def __init__(self, name: str) -> None:
        self.name = name
        self.bus: Optional[MessageBus] = None
        self.cash = 0.0

    def send(self, receiver: str, performative: Performative, conversation_id: str,
             **content: Any) -> None:
        self.bus.send(Message(self.name, receiver, performative, conversation_id, content))

    def receive(self, message: Message) -> None:
        raise NotImplementedError

    def begin_period(self, period: int) -> None:
        pass

    def end_period(self, period: int) -> None:
        pass


@dataclass
class _Procurement:
    """Buyer-side state of one one-to-many negotiation."""

    conversation_id: str
    item: str
    quantity: int
    threads: Dict[str, Negotiator]
    pending: Set[str]
    replies: Dict[str, Message] = field(default_factory=dict)
    remaining: int = 0
    round_no: int = 1
    awaiting: Set[str] = field(default_factory=set)       # sellers we sent ACCEPT to
    contracts: List[Tuple[str, Offer]] = field(default_factory=list)
    done: bool = False


class TradingAgent(Agent):
    sells: Optional[str] = None

    def __init__(self, name: str, strategy: Optional[Strategy] = None, deadline: int = 10) -> None:
        super().__init__(name)
        self.strategy = strategy or make_strategy("linear")
        self.deadline = deadline
        self.period = 0
        self.negotiation_log: List[Dict[str, Any]] = []  # one entry per procurement
        self._procurements: Dict[str, _Procurement] = {}
        self._threads: Dict[Tuple[str, str], Tuple[Negotiator, str]] = {}

    # ---- hooks for subclasses ------------------------------------------
    def buy_prefs(self, item: str) -> Preferences:
        raise NotImplementedError

    def sell_prefs(self, item: str) -> Preferences:
        raise NotImplementedError

    def available(self, item: str) -> int:
        return 0

    def on_purchase(self, item: str, seller: str, offer: Offer) -> None:
        self.cash -= offer.price * offer.quantity

    def on_sale(self, item: str, buyer: str, offer: Offer) -> None:
        self.cash += offer.price * offer.quantity

    def begin_period(self, period: int) -> None:
        self.period = period

    # ---- dispatch --------------------------------------------------------
    def receive(self, message: Message) -> None:
        procurement = self._procurements.get(message.conversation_id)
        if procurement is not None:
            self._buyer_handle(procurement, message)
        else:
            self._seller_handle(message)

    # ---- buyer role ------------------------------------------------------
    def procure(self, item: str, quantity: int) -> Optional[str]:
        """Start negotiating the purchase of ``quantity`` units of ``item``."""
        sellers = [s for s in self.bus.directory.search(f"sell:{item}") if s != self.name]
        if quantity <= 0 or not sellers:
            return None
        conversation = self.bus.new_conversation()
        prefs = self.buy_prefs(item)
        self._procurements[conversation] = _Procurement(
            conversation, item, quantity,
            {s: Negotiator(prefs, self.strategy, self.deadline, quantity) for s in sellers},
            set(sellers), remaining=quantity)
        for seller in sellers:
            self.send(seller, Performative.CFP, conversation, item=item, quantity=quantity, round=1)
        return conversation

    def _buyer_handle(self, p: _Procurement, message: Message) -> None:
        if message.performative is Performative.INFORM:
            if message.sender in p.awaiting:      # contract confirmed by the seller
                p.awaiting.discard(message.sender)
                offer = Offer.from_dict(message.content)
                if offer.quantity > 0:
                    self.on_purchase(p.item, message.sender, offer)
                    p.contracts.append((message.sender, offer))
                self._maybe_finish(p)
            return
        if message.sender not in p.pending:
            return
        p.pending.discard(message.sender)
        p.replies[message.sender] = message
        if not p.pending:
            self._close_round(p)

    def _close_round(self, p: _Procurement) -> None:
        acceptable: List[Tuple[float, str, Offer]] = []
        counters: Dict[str, Offer] = {}
        for seller, message in p.replies.items():
            negotiator = p.threads[seller]
            if message.performative is Performative.REFUSE:
                del p.threads[seller]
            elif message.performative is Performative.ACCEPT:   # seller took our offer
                offer = Offer.from_dict(message.content)
                acceptable.append((negotiator.utility(offer), seller, offer))
            elif message.performative is Performative.PROPOSE:
                offer = Offer.from_dict(message.content)
                action, counter = negotiator.respond(offer, p.round_no, offer.quantity)
                if action == ACCEPT:
                    acceptable.append((negotiator.utility(offer), seller, offer))
                elif action == PROPOSE:
                    counters[seller] = counter
        p.replies = {}

        # Sign the best acceptable offers until the order is covered; one
        # order may be split across several sellers.
        for _, seller, offer in sorted(acceptable, key=lambda c: -c[0]):
            if p.remaining <= 0:
                break
            quantity = min(offer.quantity, p.remaining)
            p.remaining -= quantity
            p.awaiting.add(seller)
            del p.threads[seller]
            self.send(seller, Performative.ACCEPT, p.conversation_id,
                      price=offer.price, delivery=offer.delivery, quantity=quantity)

        finished = p.remaining <= 0 or not counters or p.round_no >= self.deadline
        for seller in list(p.threads):
            if finished or seller not in counters:
                self.send(seller, Performative.REJECT, p.conversation_id)
                del p.threads[seller]
        if finished:
            p.done = True
            self._maybe_finish(p)
            return
        # Keep negotiating with the remaining sellers for what is still missing.
        p.round_no += 1
        p.pending = set(p.threads)
        for seller in p.threads:
            counter = counters[seller]
            self.send(seller, Performative.PROPOSE, p.conversation_id, round=p.round_no,
                      price=counter.price, delivery=counter.delivery,
                      quantity=min(counter.quantity, p.remaining))

    def _maybe_finish(self, p: _Procurement) -> None:
        if not p.done or p.awaiting:
            return
        del self._procurements[p.conversation_id]
        quantity = sum(o.quantity for _, o in p.contracts)
        success = quantity > 0
        self.negotiation_log.append({
            "period": self.period, "conversation": p.conversation_id, "buyer": self.name,
            "item": p.item, "requested": p.quantity, "success": success,
            "sellers": "+".join(s for s, _ in p.contracts) or None,
            "price": round(sum(o.price * o.quantity for _, o in p.contracts) / quantity, 2)
            if success else None,
            "delivery": max(o.delivery for _, o in p.contracts) if success else None,
            "quantity": quantity,
            "rounds": p.round_no,
        })

    # ---- seller role -----------------------------------------------------
    def _seller_handle(self, message: Message) -> None:
        key = (message.conversation_id, message.sender)
        kind = message.performative
        if kind is Performative.CFP:
            item = message.content.get("item")
            if item != self.sells or self.available(item) <= 0:
                self.send(message.sender, Performative.REFUSE, message.conversation_id)
                return
            negotiator = Negotiator(self.sell_prefs(item), self.strategy, self.deadline,
                                    int(message.content["quantity"]))
            self._threads[key] = (negotiator, item)
            self._seller_reply(key, None, int(message.content.get("round", 1)))
        elif key not in self._threads:
            return
        elif kind is Performative.PROPOSE:
            self._seller_reply(key, Offer.from_dict(message.content), int(message.content["round"]))
        elif kind is Performative.ACCEPT:
            _, item = self._threads.pop(key)
            offer = Offer.from_dict(message.content)
            shipped = Offer(offer.price, offer.delivery, min(offer.quantity, self.available(item)))
            if shipped.quantity > 0:
                self.on_sale(item, message.sender, shipped)
            self.send(message.sender, Performative.INFORM, message.conversation_id,
                      **shipped.to_dict())
        elif kind is Performative.REJECT:
            del self._threads[key]

    def _seller_reply(self, key: Tuple[str, str], counter: Optional[Offer], round_no: int) -> None:
        negotiator, item = self._threads[key]
        conversation, buyer = key
        quantity = min(negotiator.requested, self.available(item))
        action, offer = negotiator.respond(counter, round_no, quantity) if quantity > 0 \
            else ("refuse", None)
        if action == ACCEPT:
            offer = Offer(offer.price, offer.delivery, min(offer.quantity, quantity))
            self.send(buyer, Performative.ACCEPT, conversation, **offer.to_dict())
        elif action == PROPOSE:
            self.send(buyer, Performative.PROPOSE, conversation, round=round_no, **offer.to_dict())
        else:
            del self._threads[key]
            self.send(buyer, Performative.REFUSE, conversation)


class _Pipeline:
    """Goods in transit: (arrival period, quantity)."""

    def __init__(self) -> None:
        self._orders: List[Tuple[int, int]] = []

    def add(self, arrival: int, quantity: int) -> None:
        self._orders.append((arrival, quantity))

    def receive(self, period: int) -> int:
        arrived = sum(q for a, q in self._orders if a <= period)
        self._orders = [(a, q) for a, q in self._orders if a > period]
        return arrived

    @property
    def on_order(self) -> int:
        return sum(q for _, q in self._orders)


# --------------------------------------------------------------------------
# Tier 1: raw-material / component suppliers
# --------------------------------------------------------------------------
class SupplierAgent(TradingAgent):
    sells = COMPONENT
    services = (f"sell:{COMPONENT}",)

    def __init__(self, name: str, unit_cost: float, capacity: int, min_margin: float = 0.05,
                 max_markup: float = 0.6, lead_times: Tuple[int, int] = (1, MAX_LEAD_TIME), **kw: Any) -> None:
        super().__init__(name, **kw)
        self.unit_cost, self.capacity = unit_cost, capacity
        self.min_margin, self.max_markup = min_margin, max_markup
        self.lead_times = lead_times
        self.capacity_left = capacity
        self.units_sold = 0

    def begin_period(self, period: int) -> None:
        super().begin_period(period)
        self.capacity_left = self.capacity

    def available(self, item: str) -> int:
        return self.capacity_left

    def sell_prefs(self, item: str) -> Preferences:
        # A supplier prefers a high price and a long (cheap to meet) lead time.
        return Preferences(self.unit_cost * (1 + self.max_markup),
                           self.unit_cost * (1 + self.min_margin),
                           delivery_best=self.lead_times[1], delivery_worst=self.lead_times[0],
                           w_price=0.8)

    def on_sale(self, item: str, buyer: str, offer: Offer) -> None:
        super().on_sale(item, buyer, offer)
        self.capacity_left -= offer.quantity
        self.units_sold += offer.quantity
        self.cash -= self.unit_cost * offer.quantity


# --------------------------------------------------------------------------
# Tier 2: manufacturers (buy components, sell products)
# --------------------------------------------------------------------------
class ManufacturerAgent(TradingAgent):
    sells = PRODUCT
    services = (f"sell:{PRODUCT}",)

    def __init__(self, name: str, production_cost: float = 5.0, capacity: int = 60,
                 max_component_price: float = 15.0, components: int = 60, products: int = 60,
                 holding_cost: float = 0.1, min_margin: float = 0.05, max_markup: float = 0.6,
                 **kw: Any) -> None:
        super().__init__(name, **kw)
        self.production_cost, self.capacity = production_cost, capacity
        self.max_component_price = max_component_price
        self.components, self.products = components, products
        self.holding_cost = holding_cost
        self.min_margin, self.max_markup = min_margin, max_markup
        self.avg_component_cost = 0.8 * max_component_price  # belief, updated by purchases
        self.inbound = _Pipeline()
        self.units_sold = 0
        self.sales_forecast = 0.7 * capacity
        self._sold_this_period = 0

    def begin_period(self, period: int) -> None:
        super().begin_period(period)
        self._sold_this_period = 0
        self.components += self.inbound.receive(period)
        batch = max(0, min(self.components, self.capacity, 2 * self.capacity - self.products))
        self.components -= batch
        self.products += batch
        self.cash -= batch * self.production_cost

    def plan_procurement(self) -> Optional[str]:
        """Base-stock policy: cover forecast sales over the longest lead time."""
        position = self.components + self.inbound.on_order
        target = round((MAX_LEAD_TIME + 1) * self.sales_forecast)
        return self.procure(COMPONENT, target - position)

    def end_period(self, period: int) -> None:
        self.cash -= self.holding_cost * (self.components + self.products)
        self.sales_forecast += 0.3 * (self._sold_this_period - self.sales_forecast)
        # Keep a minimum activity level so a stock-out cannot starve the forecast.
        self.sales_forecast = max(self.sales_forecast, 0.3 * self.capacity)

    def available(self, item: str) -> int:
        return self.products

    def buy_prefs(self, item: str) -> Preferences:
        return Preferences(0.6 * self.max_component_price, self.max_component_price,
                           delivery_best=1, delivery_worst=MAX_LEAD_TIME, w_price=0.6)

    def sell_prefs(self, item: str) -> Preferences:
        # The selling price range follows what was actually paid upstream:
        # this is how negotiation outcomes propagate along the chain.
        unit_cost = self.avg_component_cost + self.production_cost
        return Preferences(unit_cost * (1 + self.max_markup), unit_cost * (1 + self.min_margin),
                           delivery_best=MAX_LEAD_TIME, delivery_worst=1, w_price=0.8)

    def on_purchase(self, item: str, seller: str, offer: Offer) -> None:
        super().on_purchase(item, seller, offer)
        self.inbound.add(self.period + offer.delivery, offer.quantity)
        self.avg_component_cost += 0.3 * (offer.price - self.avg_component_cost)

    def on_sale(self, item: str, buyer: str, offer: Offer) -> None:
        super().on_sale(item, buyer, offer)
        self.products -= offer.quantity
        self.units_sold += offer.quantity
        self._sold_this_period += offer.quantity


# --------------------------------------------------------------------------
# Tier 3: retailers (buy products, serve stochastic customer demand)
# --------------------------------------------------------------------------
class RetailerAgent(TradingAgent):
    def __init__(self, name: str, retail_price: float = 32.0, mean_demand: float = 40.0,
                 demand_sd: float = 8.0, stock: int = 160, holding_cost: float = 0.2,
                 min_margin: float = 0.15, rng: Optional[random.Random] = None, **kw: Any) -> None:
        super().__init__(name, **kw)
        self.retail_price, self.mean_demand, self.demand_sd = retail_price, mean_demand, demand_sd
        self.stock, self.holding_cost, self.min_margin = stock, holding_cost, min_margin
        self.rng = rng or random.Random()
        self.forecast = mean_demand
        self.inbound = _Pipeline()
        self.demand_total = self.sales_total = 0

    def begin_period(self, period: int) -> None:
        super().begin_period(period)
        self.stock += self.inbound.receive(period)

    def plan_procurement(self) -> Optional[str]:
        """Base-stock policy: cover forecast demand over the longest lead time,
        plus safety stock."""
        target = round((MAX_LEAD_TIME + 1) * self.forecast + 2 * self.demand_sd)
        return self.procure(PRODUCT, target - self.stock - self.inbound.on_order)

    def serve_customers(self) -> Tuple[int, int]:
        demand = max(0, round(self.rng.gauss(self.mean_demand, self.demand_sd)))
        sold = min(demand, self.stock)
        self.stock -= sold
        self.cash += sold * self.retail_price
        self.demand_total += demand
        self.sales_total += sold
        self.forecast += 0.3 * (demand - self.forecast)  # exponential smoothing
        return demand, sold

    def end_period(self, period: int) -> None:
        self.cash -= self.holding_cost * self.stock

    def buy_prefs(self, item: str) -> Preferences:
        reserve = self.retail_price * (1 - self.min_margin)
        return Preferences(0.55 * reserve, reserve, delivery_best=1, delivery_worst=MAX_LEAD_TIME,
                           w_price=0.6)

    def on_purchase(self, item: str, seller: str, offer: Offer) -> None:
        super().on_purchase(item, seller, offer)
        self.inbound.add(self.period + offer.delivery, offer.quantity)
