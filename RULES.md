# Global Hegemony — Rules

**Global Hegemony** is a persistent, iterated strategy game about production, predation, relative advantage, structural change, and bankruptcy.

## Player state

Each player begins the tournament with:

- **50 capital points**
- **C = 5** productive/extraction capacity (C := cooperate)
- **D = 5** predatory/coercive capacity (D := defect)

A player's internal C/D payoff structure always satisfies:

```text
C + D = 10
```

Capital and structure persist between matches. Each match receives a fresh
Environment Bank of 100 points.

## Turn sequence

1. Both players simultaneously choose **C** (cooperate) or **D** (defect).
2. The match engine resolves production, interception, raids, or weapon clash.
3. Each player pays one capital point in operating cost per turn.
4. Bankruptcy and environmental exhaustion are checked.
5. If the match continues, permitted structural modifications are resolved.

## Mutual cooperation: C/C

- If `C1 + C2 > 2`, two synergy points are added to the environment.
- A player with nonnegative C attempts to extract C points.
- A player with negative C instead loses `abs(C)` capital and extracts nothing.
- If the environment cannot satisfy both requests, the remainder is divided
  proportionally.
- Each player may modify its own structure by changing C by `-1`, `0`, or `+1`. D changes by the opposite amount.

## Unilateral defection: C/D or D/C

- The cooperator attempts production as described above.
- With nonnegative D, the defector intercepts up to D points of the harvest and also raids D capital directly from the cooperator.
- With negative D, the defector cannot intercept and instead pays `abs(D)`
  capital to the cooperator.
- One point is burned from the environment.
- The attacker may modify the victim's C by `-1`, `0`, or `+1`, with D changing the opposite amount.
- The victim may retaliate by modifying the attacker's C by `-1`, `0`, or `+1`, with D changing the opposite amount.

## Mutual defection: D/D

- Nobody extracts from the environment.
- The player with the larger D receives the difference between the two D values from the weaker player.
- Two points are burned from the environment.
- No structural C/D modifications occur.

## Bankruptcy

- A player is bankrupt at capital `<= 0`.
- If exactly one player is bankrupt, the survivor receives the remaining
  Environment Bank as the **Vulture Prize**.
- If both players go bankrupt on the same turn, neither receives the remaining environment.

## Logging

Actions are logged as `C` or `D`.

Modification values record the change applied to the target's C:

```text
+1  increase C by one
 0  no change, or no modification opportunity
-1  decrease C by one
```

The target is implied by the action outcome:

- C/C: each player modifies itself.
- C/D or D/C: each player modifies the other.
- D/D: no one is modified.
