# Memory-game-python
Memory Ball is a Python game designed to test and improve your memory skills. You must remember the position of a hidden ball within a grid to earn points. The game offers multiple difficulty levels to cater to players of different skill levels. With visually appealing designs and smooth animations, the gameplay is intuitive and engaging. Download Memory Ball now and challenge yourself to enhance your memory abilities.


# Supply-chain Multi-Agent System with automated negotiation

`supply_chain_mas/` is a separate research project in this repository: a
Multi-Agent System (MAS) in which suppliers, manufacturers and retailers are
autonomous agents that run their own tier of a supply chain and trade with
each other through **automated negotiation**. Agents are linked only by a
shared message format, so independently developed agents can join the chain.

Pure Python 3.9+, no third-party dependencies.

## Run it

```bash
python -m supply_chain_mas --periods 20 --trace
```

```bash
python -m supply_chain_mas experiment
```

```bash
python -m unittest discover -s tests
```

Options for the simulation: `--strategy {boulware,linear,conceder,tit_for_tat,mixed}`,
`--deadline N`, `--seed N`, `--no-legacy`, `--csv results.csv`.

## Architecture

| Module | Role |
| --- | --- |
| `messaging.py` | FIPA-ACL style messages (`CFP`, `PROPOSE`, `ACCEPT`, `REJECT`, `REFUSE`, `INFORM`), a queued message bus that carries only JSON, and a yellow-pages directory for service discovery |
| `negotiation.py` | Offers, private utility models, concession strategies, the `Negotiator` decision logic and a reference bilateral protocol |
| `agents.py` | `TradingAgent` (buyer and seller roles over the bus) and the three tiers: `SupplierAgent`, `ManufacturerAgent`, `RetailerAgent` |
| `external.py` | A "legacy" quotation system with its own JSON API, and the adapter agent that links it into the MAS |
| `simulation.py` | Multi-period simulation, default scenario, metrics, CSV export |
| `experiments.py` | Strategy tournament and whole-chain strategy comparison |

```
Suppliers (+ external system via adapter)  --components-->  Manufacturers  --products-->  Retailers  -->  customers
            sellers                                      buyers and sellers                 buyers
```

## The negotiation agent

* **Issues**: unit price and delivery lead time (quantity is set by the
  buyer's need and the seller's capacity).
* **Preferences**: each agent has a private linear additive utility, 1 at its
  aspiration point and 0 at its reservation point. They come from the agent's
  business state: a supplier's cost and margin, a manufacturer's actual
  purchase cost plus production cost, a retailer's shelf price.
* **Protocol**: one-to-many alternating offers. A buyer sends a call for
  proposals to every seller advertising the item, negotiates with all of them
  in parallel, signs the best acceptable offers and splits the order when one
  seller cannot cover it. Both sides have a private deadline.
* **Strategies**: time-dependent tactics (Boulware, linear, Conceder) and a
  behaviour-dependent tit-for-tat. Counter-offers are chosen on the agent's
  own iso-utility curve at the point closest to the opponent's last offer, so
  agents trade price against lead time instead of haggling on price alone.

## Linking independently developed agents

Agents never call each other; every message is serialised to JSON on the bus.
To add an agent built elsewhere, either implement `receive(message)` and
speak the six performatives, or wrap the existing system in an adapter as
`LegacySupplierAdapter` does for `LegacyQuotationSystem` (different API,
vocabulary and pricing logic). Registering the adapter under
`sell:component` is enough for the manufacturers to negotiate with it.

## Sample findings (default parameters)

Bilateral tournament, 500 random negotiations per pairing:

* Conceder against Conceder agrees most often (91%) and fastest (4 rounds);
  Boulware against Boulware agrees in 56% of cases.
* A Boulware buyer facing a Conceder seller gets the highest individual
  utility (0.47 against 0.12 for the seller).
* Linear pairings give the highest joint utility (0.71).
* Two tit-for-tat agents agree in only 29% of cases: neither leads the
  concession, so many negotiations hit the deadline.

Whole chain, 30 periods, mean of 5 seeds: Boulware, linear and tit-for-tat
all reach about 100% customer service level with similar total profit, but
linear needs about 30% fewer messages than Boulware. An all-Conceder chain
closes deals in 3 rounds but serves 95% of demand, because buyers concede to
long lead times.

These numbers come from a stylised model with made-up cost and demand
parameters; they illustrate the framework and are not empirical results.
