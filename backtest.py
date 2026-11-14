"""Local backtester used to develop the strategy in strategy.py.

It mirrors the cost model published for the eth-backtest challenge
(maker/taker fees + slippage scaled by size) with these explicit,
conservative assumptions:

  - The target position decided at the close of bar t executes at the
    OPEN of bar t+1 (market order -> taker fee; no phantom fills).
  - Taker fee: FEE_BPS basis points of traded notional (default 5 bps).
  - Slippage: linear market impact scaled by trade size relative to the
    execution bar's traded volume:
        slippage_fraction = IMPACT * |delta_position_ETH| / volume_ETH
        slippage_cost     = slippage_fraction * traded_notional
    (default IMPACT = 0.05: trading 100% of one minute's volume would
    cost 5% — deliberately harsh; the strategy must survive it.)
  - Any position still open after the last bar is closed at the final
    close, paying the same costs.
  - Equity is marked to market at every close; max drawdown is measured
    on that curve against a USD 100,000 capital base.

Usage: python3 backtest.py [bars.csv] [fee_bps] [impact]
Prints net PnL, max drawdown, cost breakdown and trade count for the
strategy in strategy.py. Pure standard library.
"""

import sys
from strategy import positions, load_bars

CAPITAL = 100_000.0


def run_backtest(bars, target_pos, fee_bps=5.0, impact=0.05, capital=CAPITAL):
    pos = 0.0
    cash = capital
    curve = []
    fees = slip = traded = 0.0
    n_trades = 0
    pending = 0.0
    for t, b in enumerate(bars):
        d = pending - pos
        if abs(d) > 1e-12:
            px = b["open"]
            notional = abs(d) * px
            fee = notional * fee_bps / 10_000.0
            s = impact * abs(d) / max(b["volume"], 1e-9) * notional
            cash -= d * px + fee + s
            fees += fee; slip += s; traded += notional; n_trades += 1
            pos = pending
        curve.append(cash + pos * b["close"])
        pending = target_pos[t]
    if abs(pos) > 1e-12:  # force-close at final close
        b = bars[-1]
        notional = abs(pos) * b["close"]
        fee = notional * fee_bps / 10_000.0
        s = impact * abs(pos) / max(b["volume"], 1e-9) * notional
        cash += pos * b["close"] - fee - s
        fees += fee; slip += s; traded += notional; n_trades += 1
        curve[-1] = cash
    peak = -1e18; max_dd = 0.0
    for e in curve:
        peak = max(peak, e)
        max_dd = max(max_dd, peak - e)
    return {
        "net_pnl": curve[-1] - capital,
        "max_drawdown": max_dd,
        "fees": fees,
        "slippage": slip,
        "trades": n_trades,
        "traded_notional": traded,
    }


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "bars.csv"
    fee = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
    imp = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
    bars = load_bars(path)
    r = run_backtest(bars, positions(bars), fee_bps=fee, impact=imp)
    print(f"net_pnl={r['net_pnl']:.2f} max_drawdown={r['max_drawdown']:.2f} "
          f"fees={r['fees']:.2f} slippage={r['slippage']:.2f} "
          f"trades={r['trades']} traded_notional={r['traded_notional']:.2f}")
