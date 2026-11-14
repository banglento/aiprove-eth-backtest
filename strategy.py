"""AIProve eth-pnl-fixed entry — Donchian breakout trend strategy.

Strategy (1-minute ETH/USDT bars):
  - Entry channel: 240 bars (4h). Exit channel: 120 bars (2h). Size: 4 ETH.
  - At the close of bar t, using only bars strictly before t:
      * if flat/short and close > highest high of the last 240 bars -> target +4 ETH
      * if flat/long  and close < lowest  low  of the last 240 bars -> target -4 ETH
      * if long  and close < lowest  low  of the last 120 bars -> target 0
      * if short and close > highest high of the last 120 bars -> target 0
    Otherwise the previous target is kept.
  - The target decided at close of bar t is the position held from bar t+1
    (execution at the next bar's open — no look-ahead, no phantom fills).

Rationale: the published cost model (taker fees + slippage scaled by trade
size relative to bar volume) punishes turnover and size, so the strategy
trades rarely (3 position changes on the frozen dataset) at a modest fixed
size, and only follows confirmed multi-hour breakouts instead of chasing
1-minute noise. Parameters sit on a broad plateau (entry 240-300 / exit
120-150 all behave similarly), which is the defence against the held-out
tail mentioned in the challenge README.

Interface:
  positions(bars) -> list[float]
      bars: list of dicts with keys open/high/low/close/volume, one per minute.
      Returns the target position in ETH (signed) for every bar, same length.
  CLI:  python3 strategy.py [bars.csv] [positions.csv]
      Writes positions.csv with columns minute,target_position_eth.
Pure Python 3 standard library. Deterministic.
"""

import csv
import sys

ENTRY = 240      # entry channel length (bars)
EXIT = 120       # exit channel length (bars)
SIZE = 4.0       # position size in ETH


def positions(bars):
    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    out = []
    pos = 0.0
    warm = max(ENTRY, EXIT)
    for t in range(len(bars)):
        if t >= warm:
            hh_e = max(highs[t - ENTRY:t])
            ll_e = min(lows[t - ENTRY:t])
            hh_x = max(highs[t - EXIT:t])
            ll_x = min(lows[t - EXIT:t])
            if pos <= 0 and closes[t] > hh_e:
                pos = SIZE
            elif pos >= 0 and closes[t] < ll_e:
                pos = -SIZE
            elif pos > 0 and closes[t] < ll_x:
                pos = 0.0
            elif pos < 0 and closes[t] > hh_x:
                pos = 0.0
        out.append(pos)
    return out


def load_bars(path):
    bars = []
    with open(path) as f:
        for row in csv.DictReader(f):
            bars.append({k: float(row[k]) for k in ("open", "high", "low", "close", "volume")})
    return bars


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "bars.csv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "positions.csv"
    bars = load_bars(src)
    pos = positions(bars)
    with open(dst, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["minute", "target_position_eth"])
        for i, p in enumerate(pos):
            w.writerow([i, f"{p:.1f}"])
    print(f"wrote {dst}: {len(pos)} bars")


if __name__ == "__main__":
    main()
