"""
Build a comps input file from live market data with yfinance.

Usage:
    pip install yfinance
    python fetch_data.py TARGET PEER1 PEER2 ... > data/my_peer_set.csv

Example:
    python fetch_data.py VNT FTV AME ROP KEYS > data/vontier_peers.csv

Figures come from Yahoo Finance and use trailing twelve month revenue and
EBITDA. Check them against company filings before relying on them.
"""

import csv
import sys


def fetch(ticker: str) -> dict:
    import yfinance as yf

    info = yf.Ticker(ticker).info
    revenue = info.get("totalRevenue")
    return {
        "ticker": ticker.upper(),
        "name": info.get("shortName", ticker.upper()),
        "share_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "shares_out": (info.get("sharesOutstanding") or 0) / 1e6,
        "total_debt": (info.get("totalDebt") or 0) / 1e6,
        "cash": (info.get("totalCash") or 0) / 1e6,
        "revenue": (revenue or 0) / 1e6,
        "ebitda": (info.get("ebitda") or 0) / 1e6,
        "eps_fwd": info.get("forwardEps") or 0,
        "revenue_growth": info.get("revenueGrowth") or 0,
    }


def main(tickers: list[str]) -> None:
    if len(tickers) < 3:
        sys.exit("Give a target ticker followed by at least two peers")
    fields = ["ticker", "name", "role", "share_price", "shares_out", "total_debt",
              "cash", "revenue", "ebitda", "eps_fwd", "revenue_growth"]
    writer = csv.DictWriter(sys.stdout, fieldnames=fields)
    writer.writeheader()
    for i, t in enumerate(tickers):
        row = fetch(t)
        row["role"] = "target" if i == 0 else "peer"
        writer.writerow(row)


if __name__ == "__main__":
    main(sys.argv[1:])
