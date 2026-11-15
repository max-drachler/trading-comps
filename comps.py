"""
Trading comparables (comps) analysis.

Calculates market cap, enterprise value and valuation multiples for a peer
set, summarizes the multiples, and applies the peer range to a target
company to produce an implied valuation range.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

MULTIPLES = ["EV / Revenue", "EV / EBITDA", "P / E (Fwd)"]


def load(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"ticker", "name", "role", "share_price", "shares_out", "total_debt",
                "cash", "revenue", "ebitda", "eps_fwd"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    return df


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add market cap, enterprise value, multiples and operating metrics."""
    out = df.copy()
    out["Market Cap"] = out["share_price"] * out["shares_out"]
    out["Enterprise Value"] = out["Market Cap"] + out["total_debt"] - out["cash"]
    out["EBITDA Margin"] = out["ebitda"] / out["revenue"]
    out["EV / Revenue"] = out["Enterprise Value"] / out["revenue"]
    # Multiples on negative EBITDA or earnings are not meaningful
    out["EV / EBITDA"] = (out["Enterprise Value"] / out["ebitda"]).where(out["ebitda"] > 0)
    out["P / E (Fwd)"] = (out["share_price"] / out["eps_fwd"]).where(out["eps_fwd"] > 0)
    return out


def summary(peers: pd.DataFrame) -> pd.DataFrame:
    """Max, 75th percentile, mean, median, 25th percentile and min of each multiple."""
    m = peers[MULTIPLES]
    return pd.DataFrame({
        "Max": m.max(),
        "75th Pct": m.quantile(0.75),
        "Mean": m.mean(),
        "Median": m.median(),
        "25th Pct": m.quantile(0.25),
        "Min": m.min(),
    }).T


def implied_valuation(target: pd.Series, stats: pd.DataFrame) -> pd.DataFrame:
    """Apply the peer 25th to 75th percentile range to the target.

    EV multiples imply enterprise value, which is bridged to equity value by
    subtracting debt and adding cash. P/E implies the share price directly.
    """
    rows = []
    for multiple, metric in (("EV / Revenue", "revenue"), ("EV / EBITDA", "ebitda")):
        for label in ("25th Pct", "Median", "75th Pct"):
            ev = stats.loc[label, multiple] * target[metric]
            equity = ev - target["total_debt"] + target["cash"]
            rows.append((multiple, label, equity / target["shares_out"]))
    for label in ("25th Pct", "Median", "75th Pct"):
        rows.append(("P / E (Fwd)", label, stats.loc[label, "P / E (Fwd)"] * target["eps_fwd"]))
    long = pd.DataFrame(rows, columns=["Multiple", "Point", "Implied Share Price"])
    return long.pivot(index="Multiple", columns="Point", values="Implied Share Price")[
        ["25th Pct", "Median", "75th Pct"]
    ].loc[MULTIPLES]


def run(path: str | Path) -> dict:
    df = add_metrics(load(path))
    target_rows = df[df["role"] == "target"]
    if len(target_rows) != 1:
        raise ValueError("Exactly one row must have role = target")
    target = target_rows.iloc[0]
    peers = df[df["role"] == "peer"].set_index("ticker")
    stats = summary(peers)
    return {
        "target": target,
        "peers": peers,
        "summary": stats,
        "implied": implied_valuation(target, stats),
    }
