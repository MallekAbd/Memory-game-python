"""Linking an independently developed system into the MAS.

:class:`LegacyQuotationSystem` stands for software built by another team with
no knowledge of this framework: it has its own JSON API, its own vocabulary
(``sku``, ``lead_weeks``, ``unit_price``) and a rule-based pricing policy
instead of utility functions.

:class:`LegacySupplierAdapter` is a thin agent that translates between the
shared negotiation messages and that API.  Nothing else in the supply chain
changes: the adapter advertises ``sell:component`` in the directory and the
manufacturers negotiate with it exactly as with native suppliers.  The same
pattern links any external agent (a web service, another agent platform, ...).
"""

from __future__ import annotations

import json
from typing import Dict, Tuple

from .agents import COMPONENT, Agent
from .messaging import Message, Performative


class LegacyQuotationSystem:
    """Third-party order desk: price list, expedite fee, stepwise discounts."""

    def __init__(self, list_price: float = 14.5, floor_price: float = 11.0,
                 unit_cost: float = 9.8, weekly_capacity: int = 30,
                 expedite_fee: float = 0.5, discount_step: float = 0.6,
                 standard_lead_weeks: int = 3, max_requotes: int = 6) -> None:
        self.list_price, self.floor_price, self.unit_cost = list_price, floor_price, unit_cost
        self.weekly_capacity, self.expedite_fee = weekly_capacity, expedite_fee
        self.discount_step, self.standard_lead_weeks = discount_step, standard_lead_weeks
        self.max_requotes = max_requotes
        self.free_capacity = weekly_capacity
        self.revenue = self.costs = 0.0

    def new_week(self) -> None:
        self.free_capacity = self.weekly_capacity

    def _surcharge(self, lead_weeks: int) -> float:
        return self.expedite_fee * max(0, self.standard_lead_weeks - lead_weeks)

    def quote(self, request_json: str) -> str:
        """``{"sku", "qty", "lead_weeks"?, "requote"?}`` -> quotation or decline."""
        request = json.loads(request_json)
        requote = int(request.get("requote", 0))
        qty = min(int(request["qty"]), self.free_capacity)
        if request.get("sku") != "CMP-STD" or qty <= 0 or requote > self.max_requotes:
            return json.dumps({"status": "declined"})
        lead = max(1, int(request.get("lead_weeks", self.standard_lead_weeks)))
        surcharge = self._surcharge(lead)
        price = max(self.floor_price, self.list_price - self.discount_step * requote) + surcharge
        return json.dumps({"status": "quoted", "unit_price": round(price, 2), "qty": qty,
                           "lead_weeks": lead, "min_price": self.floor_price + surcharge})

    def book(self, order_json: str) -> str:
        order = json.loads(order_json)
        qty = min(int(order["qty"]), self.free_capacity)
        self.free_capacity -= qty
        self.revenue += qty * float(order["unit_price"])
        self.costs += qty * self.unit_cost
        return json.dumps({"status": "booked" if qty else "declined", "qty": qty})


class LegacySupplierAdapter(Agent):
    """Wraps a :class:`LegacyQuotationSystem` as a component-selling agent."""

    services = (f"sell:{COMPONENT}",)

    def __init__(self, name: str, system: LegacyQuotationSystem) -> None:
        super().__init__(name)
        self.system = system
        self._requotes: Dict[Tuple[str, str], int] = {}

    def begin_period(self, period: int) -> None:
        self.system.new_week()
        self.cash = self.system.revenue - self.system.costs

    def end_period(self, period: int) -> None:
        self.cash = self.system.revenue - self.system.costs

    @property
    def units_sold(self) -> int:
        return round(self.system.costs / self.system.unit_cost)

    def receive(self, message: Message) -> None:
        key = (message.conversation_id, message.sender)
        content, kind = message.content, message.performative
        if kind is Performative.CFP:
            if content.get("item") != COMPONENT:
                self.send(message.sender, Performative.REFUSE, message.conversation_id)
                return
            self._requotes[key] = 0
            self._quote(key, {"sku": "CMP-STD", "qty": content["quantity"]}, None,
                        int(content.get("round", 1)))
        elif key not in self._requotes:
            return
        elif kind is Performative.PROPOSE:
            self._requotes[key] += 1
            self._quote(key, {"sku": "CMP-STD", "qty": content["quantity"],
                              "lead_weeks": content["delivery"],
                              "requote": self._requotes[key]}, content, int(content["round"]))
        elif kind is Performative.ACCEPT:
            del self._requotes[key]
            booked = json.loads(self.system.book(json.dumps(
                {"qty": content["quantity"], "unit_price": content["price"]})))
            self.send(message.sender, Performative.INFORM, message.conversation_id,
                      price=content["price"], delivery=content["delivery"],
                      quantity=booked["qty"])
        elif kind is Performative.REJECT:
            del self._requotes[key]

    def _quote(self, key: Tuple[str, str], request: dict, counter: dict, round_no: int) -> None:
        conversation, buyer = key
        reply = json.loads(self.system.quote(json.dumps(request)))
        if reply["status"] != "quoted":
            del self._requotes[key]
            self.send(buyer, Performative.REFUSE, conversation)
        elif counter is not None and counter["price"] >= reply["min_price"]:
            self.send(buyer, Performative.ACCEPT, conversation, price=counter["price"],
                      delivery=reply["lead_weeks"], quantity=reply["qty"])
        else:
            self.send(buyer, Performative.PROPOSE, conversation, round=round_no,
                      price=reply["unit_price"], delivery=reply["lead_weeks"],
                      quantity=reply["qty"])
