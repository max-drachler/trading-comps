# Trading Comps Analysis

A trading comparables tool in Python. Give it a target company and a peer set, and it calculates enterprise value and valuation multiples for each peer, summarizes the peer range, and applies that range to the target to produce an implied share price range and a football field chart.

## What it does

1. **Builds the comps table.** Market cap, enterprise value, revenue growth, EBITDA margin, EV / Revenue, EV / EBITDA and forward P / E for each peer.
2. **Handles bad data.** Multiples on negative EBITDA or earnings are marked N/M and excluded from the summary statistics, the same way a banker would treat them.
3. **Summarizes the peer set.** Max, 75th percentile, mean, median, 25th percentile and min for each multiple.
4. **Values the target.** Applies the 25th to 75th percentile range of each multiple to the target. EV multiples are bridged to equity value (less debt, plus cash) before dividing by shares.
5. **Charts the results.** A football field of the implied ranges, and a growth vs multiple scatter that shows whether the target is cheap or expensive relative to how fast it grows.
6. **Pulls live data (optional).** `fetch_data.py` builds an input file for any set of public tickers using Yahoo Finance.

## Example output

The example uses a hypothetical target and eight illustrative peers. The figures are not real companies.

| Multiple | 25th Pct | Median | 75th Pct |
|---|---|---|---|
| EV / Revenue | 2.9x | 3.4x | 3.8x |
| EV / EBITDA | 14.1x | 16.4x | 16.9x |
| P / E (Fwd) | 17.3x | 21.1x | 21.5x |

Peer F has negative EBITDA and earnings, so its EV / EBITDA and P / E are N/M and excluded.

**Implied share price for Target Co. (currently $42.00)**

| Multiple | 25th Pct | Median | 75th Pct |
|---|---|---|---|
| EV / Revenue | $39.00 | $47.26 | $53.70 |
| EV / EBITDA | $38.40 | $45.45 | $46.95 |
| P / E (Fwd) | $39.81 | $48.42 | $49.46 |

~~~mermaid
xychart-beta
    title "EV / EBITDA by company, sorted by revenue growth"
    x-axis ["PRD 4%", "PRG 6%", "PRB 7%", "TGT 9%", "PRE 10%", "PRA 11%", "PRH 12%", "PRC 15%"]
    y-axis "EV / EBITDA (x)" 0 --> 22
    bar [12.0, 13.0, 15.1, 15.3, 16.8, 16.4, 17.0, 20.0]
~~~

Running `python run.py` also saves a football field chart and a growth vs multiple scatter to `output/`.

**Takeaway:** The target trades at 15.3x EBITDA against a peer median of 16.4x, and every method's median sits above the current $42.00 price. The chart above shows the gap is modest: the target's 9% growth puts it between peers trading at 15x and 17x, so the market is roughly pricing it in line with its growth. EV / EBITDA is the most reliable method here because margins vary widely across the peer set, which distorts EV / Revenue.

## How to run

~~~bash
pip install -r requirements.txt
python run.py                          # runs the example peer set
python run.py data/my_peer_set.csv     # runs your own peer set
pytest                                 # runs the tests
~~~

To run it on real companies:

~~~bash
pip install yfinance
python fetch_data.py VNT FTV AME ROP KEYS > data/vontier_peers.csv
python run.py data/vontier_peers.csv
~~~

The first ticker is the target and the rest are peers. Always check fetched figures against company filings.

## Input format

One row per company, in $ millions except per share figures. Exactly one row must have `role` set to `target`.

| Column | Meaning |
|---|---|
| `ticker`, `name` | Identifiers |
| `role` | `target` or `peer` |
| `share_price` | Current share price ($) |
| `shares_out` | Diluted shares outstanding (mm) |
| `total_debt`, `cash` | Balance sheet ($mm) |
| `revenue`, `ebitda` | Last twelve months ($mm) |
| `eps_fwd` | Next twelve months EPS ($) |
| `revenue_growth` | Revenue growth (decimal) |

## Files

| File | Purpose |
|---|---|
| `comps.py` | Analysis logic: metrics, summary statistics, implied valuation |
| `run.py` | Runs the analysis, prints tables, saves CSVs and charts to `output/` |
| `fetch_data.py` | Builds an input file from live market data |
| `data/example_peers.csv` | Example peer set |
| `tests/test_comps.py` | Checks EV math, N/M handling and the equity bridge |
