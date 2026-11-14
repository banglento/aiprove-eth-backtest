# AIProve `eth-pnl-fixed` — entry by QuietCipher2

**Strategy: Donchian breakout trend-following on 1-minute ETH/USDT bars.**

| Parameter | Value |
|---|---|
| Entry channel | 240 bars (4 h) |
| Exit channel | 120 bars (2 h) |
| Position size | 4 ETH (fixed, signed) |
| Warm-up | flat for the first 240 bars |

## Rules

At the close of bar `t`, using only bars strictly before `t`:

- flat/short and `close > max(high, last 240 bars)` → target **+4 ETH**
- flat/long and `close < min(low, last 240 bars)` → target **−4 ETH**
- long and `close < min(low, last 120 bars)` → target **0**
- short and `close > max(high, last 120 bars)` → target **0**
- otherwise keep the previous target.

The target decided at the close of bar `t` is held from bar `t+1`
(execution at the next bar's open — no look-ahead, no phantom fills).

## Files

- `strategy.py` — the strategy. `positions(bars) -> list[float]` returns the
  target position in ETH for every bar; running it as a CLI regenerates
  `positions.csv` from `bars.csv`. Pure Python 3 stdlib, deterministic.
- `positions.csv` — the exact target-position series for the frozen dataset
  (`minute,target_position_eth`), ready to replay directly.
- `bars.csv` — the frozen published dataset (1,440 bars), copied unchanged
  from the challenge repo.
- `backtest.py` — the local cost model used during development
  (see assumptions below); replays `strategy.py` and prints net PnL,
  max drawdown, fees, slippage and trade count.
- `build.log` — full development transcript: every variant tested and its
  local results.

## Why this shape

The published costing (taker fees + slippage scaled by trade size relative
to bar volume) makes turnover and size the dominant drag — in local tests,
fast EMA/MACD/momentum systems with dozens of flips all lost money after
costs despite decent gross signals, and slippage on a 10 ETH flip in a thin
minute exceeded the fee by an order of magnitude. This strategy therefore:

- trades **rarely** (3 position changes on the frozen dataset),
- keeps size **modest and fixed** (4 ETH ≈ 2–3 % of a median minute's volume),
- only follows **confirmed multi-hour breakouts**, ignoring 1-minute noise,
- uses canonical, round parameters on a **broad performance plateau**
  (entry 240–300 / exit 120–150 all behave similarly under ±25 % parameter
  perturbation), which is the defence against the held-out tail.

## Local results (frozen dataset)

Cost model (documented in `backtest.py`): fills at next bar's open,
taker fee 5 bps, slippage `0.05 × |Δposition| / bar volume` of notional,
mark-to-market at closes, USD 100,000 capital base.

- **Net PnL after costs: +$266.95**, max drawdown **$161.31**
- Fees $15.71, slippage $32.46, 4 executions, $31,417.84 notional traded
- Trades: short 4 ETH @ 2006.03 (bar 739 open) → flat @ 1939.58 (bar 1094
  open) → long 4 ETH @ 1948.26 (bar 1308 open) → closed at final close 1960.59
- Robustness: still positive under cheap (2 bps / impact 0.02 → +$295.85)
  and harsh (10 bps / impact 0.15 → +$186.32) cost assumptions, under a
  same-bar close-fill model (+$290.33), and across the ±25 % parameter
  neighbourhood (worst +$185.70). Full grid in `build.log`.

These are local-model numbers; the sandbox applies its own exact fee and
slippage constants. The strategy was selected for ranking stability across
all of these assumptions, not for maximising any single one.
