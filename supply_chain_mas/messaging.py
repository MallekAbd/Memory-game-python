"""Agent communication layer.

Agents never call each other directly.  They exchange FIPA-ACL style messages
through a :class:`MessageBus`, and discover each other through a
:class:`DirectoryFacilitator` (yellow pages).  Every message is serialised to
JSON on the bus, so the only contract between agents is the wire format: an
agent written by another team (or in another language, behind an adapter) can
join the supply chain as long as it speaks the same messages.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Deque, Dict, Iterable, List, Protocol


class Performative(str, Enum):
    """Speech acts used by the negotiation protocol (subset of FIPA-ACL)."""

    CFP = "cfp"          # buyer -> seller : call for proposals
    PROPOSE = "propose"  # either way      : offer / counter-offer
    ACCEPT = "accept"    # either way      : accept the other side's last offer
    REJECT = "reject"    # buyer -> seller : negotiation closed without a deal
    REFUSE = "refuse"    # seller -> buyer : seller withdraws
    INFORM = "inform"    # seller -> buyer : order booked (final contract)


@dataclass(frozen=True)
class Message:
    sender: str
    receiver: str
    performative: Performative
    conversation_id: str
    content: Dict[str, Any] = field(default_factory=dict)
    protocol: str = "alternating-offers"
    ontology: str = "supply-chain"

    def to_json(self) -> str:
        data = asdict(self)
        data["performative"] = self.performative.value
        return json.dumps(data, sort_keys=True)

    @classmethod
    def from_json(cls, raw: str) -> "Message":
        data = json.loads(raw)
        data["performative"] = Performative(data["performative"])
        return cls(**data)

    def __str__(self) -> str:
        body = ", ".join(f"{k}={v}" for k, v in self.content.items())
        return (f"[{self.conversation_id}] {self.sender:>14} -> {self.receiver:<14} "
                f"{self.performative.value.upper():<8} {body}")


class Addressable(Protocol):
    name: str

    def receive(self, message: Message) -> None: ...


class DirectoryFacilitator:
    """Yellow pages: agents advertise services, others look them up."""

    def __init__(self) -> None:
        self._services: Dict[str, List[str]] = {}

    def advertise(self, agent_name: str, service: str) -> None:
        providers = self._services.setdefault(service, [])
        if agent_name not in providers:
            providers.append(agent_name)

    def search(self, service: str) -> List[str]:
        return list(self._services.get(service, []))


class MessageBus:
    """Asynchronous (queued) message transport shared by all agents."""

    def __init__(self) -> None:
        self.directory = DirectoryFacilitator()
        self.log: List[Message] = []
        self._agents: Dict[str, Addressable] = {}
        self._queue: Deque[str] = deque()
        self._conversations = 0

    def register(self, agent: Addressable, services: Iterable[str] = ()) -> None:
        if agent.name in self._agents:
            raise ValueError(f"agent name already registered: {agent.name}")
        self._agents[agent.name] = agent
        for service in services:
            self.directory.advertise(agent.name, service)
        if hasattr(agent, "bus"):
            agent.bus = self

    def new_conversation(self) -> str:
        self._conversations += 1
        return f"c{self._conversations:04d}"

    def send(self, message: Message) -> None:
        if message.receiver not in self._agents:
            raise KeyError(f"unknown receiver: {message.receiver}")
        self._queue.append(message.to_json())  # only JSON crosses the bus

    def run(self, max_messages: int = 1_000_000) -> int:
        """Deliver queued messages until the system is quiescent."""
        delivered = 0
        while self._queue:
            if delivered >= max_messages:
                raise RuntimeError("message limit exceeded (livelock?)")
            message = Message.from_json(self._queue.popleft())
            self.log.append(message)
            self._agents[message.receiver].receive(message)
            delivered += 1
        return delivered
