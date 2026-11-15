"""
Run the comps analysis and save the outputs.

Usage:
    python run.py                         # uses data/example_peers.csv
    python run.py data/my_peer_set.csv    # uses your own peer set
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import comps

OUT = Path(__file__).parent / "output"


def fmt_x(v) -> str:
    return "N/M" if pd.isna(v) else f"{v:.1f}x"


def main(path: str = "data/example_peers.csv") -> None:
    res = comps.run(path)
    OUT.mkdir(exist_ok=True)
    target, peers, stats, implied = res["target"], res["peers"], res["summary"], res["implied"]

    print(f"\nTrading Comps: {target['name']}  ($ in millions, except per share)\n")
    table = peers[["name", "Market Cap", "Enterprise Value", "revenue_growth", "EBITDA Margin"] + comps.MULTIPLES].copy()
    table.columns = ["Company", "Mkt Cap", "EV", "Rev Growth", "EBITDA Mgn"] + comps.MULTIPLES
    display = table.copy().astype(object)
    display["Mkt Cap"] = table["Mkt Cap"].map(lambda v: f"{v:,.0f}")
    display["EV"] = table["EV"].map(lambda v: f"{v:,.0f}")
    display["Rev Growth"] = table["Rev Growth"].map(lambda v: f"{v:.0%}")
    display["EBITDA Mgn"] = table["EBITDA Mgn"].map(lambda v: f"{v:.0%}")
    for m in comps.MULTIPLES:
        display[m] = table[m].map(fmt_x)
    print(display.to_string())
    print()
    print("Peer multiple summary")
    print(stats.map(fmt_x).to_string())
    print()

    current = target["share_price"]
    print(f"Implied share price for {target['name']} (current ${current:.2f})")
    print(implied.map(lambda v: f"${v:,.2f}").to_string())
    print()

    table.to_csv(OUT / "comps_table.csv")
    stats.round(2).to_csv(OUT / "summary_stats.csv")
    implied.round(2).to_csv(OUT / "implied_valuation.csv")

    # Football field: 25th to 75th percentile range with the median marked
    fig, ax = plt.subplots(figsize=(8, 3.6))
    labels = list(implied.index)[::-1]
    for i, m in enumerate(labels):
        lo, med, hi = implied.loc[m, ["25th Pct", "Median", "75th Pct"]]
        ax.barh(i, hi - lo, left=lo, color="#9fb8d6", height=0.5)
        ax.plot([med, med], [i - 0.25, i + 0.25], color="#1f4e79", lw=2)
        ax.text(lo - 0.6, i, f"${lo:.0f}", va="center", ha="right", fontsize=9)
        ax.text(hi + 0.6, i, f"${hi:.0f}", va="center", ha="left", fontsize=9)
    ax.axvline(current, color="#c0504d", ls="--", lw=1.5)
    ax.text(current, len(labels) - 0.45, f"Current ${current:.2f}", color="#c0504d",
            ha="center", fontsize=9)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Implied share price ($)")
    ax.set_title(f"{target['name']}: valuation range (peer 25th to 75th percentile)")
    ax.set_ylim(-0.6, len(labels) - 0.2)
    lo_all, hi_all = implied.values.min(), implied.values.max()
    pad = (hi_all - lo_all) * 0.2
    ax.set_xlim(min(lo_all, current) - pad, max(hi_all, current) + pad)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "football_field.png", dpi=150)
    plt.close(fig)

    # Growth vs multiple scatter: do faster growers trade at higher multiples?
    valid = peers.dropna(subset=["EV / EBITDA"])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(valid["revenue_growth"] * 100, valid["EV / EBITDA"], color="#1f4e79")
    for t, row in valid.iterrows():
        ax.annotate(t, (row["revenue_growth"] * 100, row["EV / EBITDA"]),
                    textcoords="offset points", xytext=(5, 4), fontsize=9)
    target_ev_ebitda = (target["share_price"] * target["shares_out"] + target["total_debt"]
                        - target["cash"]) / target["ebitda"]
    ax.scatter([target["revenue_growth"] * 100], [target_ev_ebitda], color="#c0504d", marker="D")
    ax.annotate(f"{target['ticker']} (target)", (target["revenue_growth"] * 100, target_ev_ebitda),
                textcoords="offset points", xytext=(5, 4), fontsize=9, color="#c0504d")
    ax.set_xlabel("Revenue growth (%)")
    ax.set_ylabel("EV / EBITDA (x)")
    ax.set_title("Growth vs valuation")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "growth_vs_multiple.png", dpi=150)
    plt.close(fig)

    print(f"Outputs saved to {OUT}/")


if __name__ == "__main__":
    main(*sys.argv[1:])
