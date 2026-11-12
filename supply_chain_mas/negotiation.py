"""Automated negotiation core: offers, utilities, strategies and protocol.

Negotiations are multi-issue (unit price and delivery lead time) and follow
the alternating-offers protocol under a private deadline.  Each side owns

* :class:`Preferences` - a private, linear additive utility model, and
* :class:`Strategy`    - a concession tactic giving the utility level the
  agent demands at each moment of the negotiation.

A :class:`Negotiator` combines both and decides, for every incoming offer,
whether to accept, counter-offer or walk away.  Counter-offers are picked on
the agent's own iso-utility curve at the point closest to the opponent's last
offer (a trade-off heuristic that finds win-win deals across issues).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

ACCEPT, PROPOSE, REFUSE = "accept", "propose", "refuse"


@dataclass(frozen=True)
class Offer:
    price: float     # unit price
    delivery: int    # lead time in periods
    quantity: int

    def to_dict(self) -> Dict[str, Any]:
        return {"price": self.price, "delivery": self.delivery, "quantity": self.quantity}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Offer":
        return cls(float(data["price"]), int(data["delivery"]), int(data["quantity"]))


@dataclass(frozen=True)
class Preferences:
    """Private preferences of one side.

    ``*_best`` is the aspiration value and ``price_reserve`` / ``delivery_worst``
    the walk-away value.  The same class serves both roles: a buyer has
    ``price_best < price_reserve``, a seller the opposite.  Utility is 1 at the
    aspiration point, 0 at the reservation point and negative beyond it.
    """

    price_best: float
    price_reserve: float
    delivery_best: int
    delivery_worst: int
    w_price: float = 0.7             # weight of price; delivery gets 1 - w_price

    def __post_init__(self) -> None:
        if self.price_best == self.price_reserve:
            raise ValueError("price_best and price_reserve must differ")
        if not 0.0 < self.w_price <= 1.0:
            raise ValueError("w_price must be in (0, 1]")

    def _u_price(self, price: float) -> float:
        return min(1.0, (price - self.price_reserve) / (self.price_best - self.price_reserve))

    def _u_delivery(self, delivery: int) -> float:
        span = self.delivery_best - self.delivery_worst
        if span == 0:
            return 1.0
        return min(1.0, (delivery - self.delivery_worst) / span)

    def utility(self, offer: Offer) -> float:
        return self.w_price * self._u_price(offer.price) \
            + (1.0 - self.w_price) * self._u_delivery(offer.delivery)

    def make_offer(self, target: float, quantity: int, toward: Optional[Offer] = None) -> Offer:
        """Build an offer worth ``target`` utility to us, as attractive as
        possible to the opponent (closest to their last offer ``toward``)."""
        lo, hi = sorted((self.delivery_best, self.delivery_worst))
        candidates: List[Tuple[float, Offer]] = []
        for delivery in range(lo, hi + 1):
            needed = (target - (1.0 - self.w_price) * self._u_delivery(delivery)) / self.w_price
            needed = min(1.0, max(0.0, needed))  # never price beyond our reservation
            price = round(self.price_reserve + needed * (self.price_best - self.price_reserve), 2)
            offer = Offer(price, delivery, quantity)
            candidates.append((self.utility(offer), offer))
        good = [c for c in candidates if c[0] >= target - 1e-3]
        if not good:
            good = [max(candidates, key=lambda c: c[0])]
        if toward is None:
            return max(good, key=lambda c: self._u_delivery(c[1].delivery))[1]
        price_span = abs(self.price_best - self.price_reserve)
        delivery_span = max(1, hi - lo)

        def distance(c: Tuple[float, Offer]) -> float:
            return (abs(c[1].price - toward.price) / price_span
                    + abs(c[1].delivery - toward.delivery) / delivery_span)

        return min(good, key=distance)[1]


# --------------------------------------------------------------------------
# Concession strategies
# --------------------------------------------------------------------------
class Strategy:
    """Maps negotiation state to the utility the agent currently demands."""

    name = "strategy"

    def target(self, t: float, negotiator: "Negotiator") -> float:
        raise NotImplementedError


class TimeDependent(Strategy):
    """Faratin et al. time-dependent tactic.

    ``target(t) = u_min + (1 - u_min) * (1 - t ** (1 / e))`` with ``t`` in [0, 1].
    ``e < 1`` is *Boulware* (concede late), ``e = 1`` linear,
    ``e > 1`` *Conceder* (concede early).
    """

    def __init__(self, e: float, u_min: float = 0.05, name: Optional[str] = None) -> None:
        if e <= 0:
            raise ValueError("e must be positive")
        self.e, self.u_min = e, u_min
        self.name = name or f"time-dependent(e={e})"

    def target(self, t: float, negotiator: "Negotiator") -> float:
        t = min(1.0, max(0.0, t))
        return self.u_min + (1.0 - self.u_min) * (1.0 - t ** (1.0 / self.e))


class TitForTat(Strategy):
    """Behaviour-dependent tactic: reciprocate the opponent's last concession
    (measured in our own utility), with a small unconditional step so that two
    tit-for-tat agents do not stall."""

    name = "tit_for_tat"

    def __init__(self, u_min: float = 0.05, min_step: float = 0.02) -> None:
        self.u_min, self.min_step = u_min, min_step

    def target(self, t: float, negotiator: "Negotiator") -> float:
        if not negotiator.own_targets:
            return 1.0
        concession = 0.0
        if len(negotiator.opp_utils) >= 2:
            concession = max(0.0, negotiator.opp_utils[-1] - negotiator.opp_utils[-2])
        return max(self.u_min, negotiator.own_targets[-1] - max(concession, self.min_step))


STRATEGIES = ("boulware", "linear", "conceder", "tit_for_tat")


def make_strategy(name: str) -> Strategy:
    if name == "boulware":
        return TimeDependent(0.3, name="boulware")
    if name == "linear":
        return TimeDependent(1.0, name="linear")
    if name == "conceder":
        return TimeDependent(3.0, name="conceder")
    if name == "tit_for_tat":
        return TitForTat()
    raise ValueError(f"unknown strategy {name!r}; choose from {STRATEGIES}")


# --------------------------------------------------------------------------
# Decision making for one side of one bilateral negotiation thread
# --------------------------------------------------------------------------
class Negotiator:
    def __init__(self, prefs: Preferences, strategy: Strategy, deadline: int,
                 requested: int) -> None:
        self.prefs, self.strategy = prefs, strategy
        self.deadline, self.requested = max(1, deadline), requested
        self.own_targets: List[float] = []
        self.opp_utils: List[float] = []

    def utility(self, offer: Offer) -> float:
        return self.prefs.utility(offer)

    def respond(self, opp_offer: Optional[Offer], round_no: int,
                quantity: int) -> Tuple[str, Optional[Offer]]:
        """Return ``(ACCEPT, opp_offer)``, ``(PROPOSE, counter)`` or ``(REFUSE, None)``."""
        if round_no > self.deadline:
            return REFUSE, None
        if opp_offer is not None:
            self.opp_utils.append(self.utility(opp_offer))
        target = self.strategy.target(round_no / self.deadline, self)
        self.own_targets.append(target)
        if opp_offer is not None and self.opp_utils[-1] >= max(0.0, target - 1e-9):
            return ACCEPT, opp_offer
        return PROPOSE, self.prefs.make_offer(target, quantity, toward=opp_offer)


@dataclass(frozen=True)
class Outcome:
    agreed: bool
    offer: Optional[Offer]
    rounds: int
    buyer_utility: float = 0.0
    seller_utility: float = 0.0


def run_bilateral(buyer: Negotiator, seller: Negotiator, quantity: int) -> Outcome:
    """Reference implementation of the protocol for one buyer and one seller
    (the trading agents run exactly this exchange over the message bus)."""

    def deal(offer: Offer, rounds: int) -> Outcome:
        return Outcome(True, offer, rounds, buyer.utility(offer), seller.utility(offer))

    counter: Optional[Offer] = None
    round_no = 1
    while True:
        action, offer = seller.respond(counter, round_no, quantity)
        if action == REFUSE:
            return Outcome(False, None, round_no)
        if action == ACCEPT:
            return deal(counter, round_no)
        action, counter = buyer.respond(offer, round_no, offer.quantity)
        if action == ACCEPT:
            return deal(offer, round_no)
        if action == REFUSE or round_no >= buyer.deadline:
            return Outcome(False, None, round_no)
        round_no += 1
