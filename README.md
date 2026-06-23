# Global Hegemony

A small, dependency-free Python implementation of the Global Hegemony strategy game.

## Run a match

From the project root:

```bash
python3 main.py
```

This prints a compact turn table and writes a detailed CSV log to:

```text
global_hegemony_match_log.csv
```

## Run tests

```bash
python3 -m unittest discover -s tests
```

## Add a strategy

Create a new module in `global_hegemony/strategies/`, subclass `Player`, and implement `choose_action`. 

Override either modification method when needed.

```python
from global_hegemony.models import Action, GameView, Modification
from global_hegemony.player import Player


class MyStrategy(Player):
    def choose_action(self, view: GameView) -> Action:
        return Action.COOPERATE

    def choose_self_modification(self, view: GameView) -> Modification:
        return Modification.NO_CHANGE

    def choose_opponent_modification(self, view: GameView) -> Modification:
        return Modification.NO_CHANGE
```
