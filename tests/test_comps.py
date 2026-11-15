import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comps  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data" / "example_peers.csv"


@pytest.fixture
def res():
    return comps.run(DATA)


def test_enterprise_value(res):
    a = res["peers"].loc["PRA"]
    assert a["Market Cap"] == pytest.approx(97.26 * 95)
    assert a["Enterprise Value"] == pytest.approx(97.26 * 95 + 900 - 300)


def test_negative_ebitda_is_not_meaningful(res):
    f = res["peers"].loc["PRF"]
    assert pd.isna(f["EV / EBITDA"])
    assert pd.isna(f["P / E (Fwd)"])
    assert not pd.isna(f["EV / Revenue"])


def test_summary_excludes_nm_values(res):
    valid = res["peers"]["EV / EBITDA"].dropna()
    assert res["summary"].loc["Median", "EV / EBITDA"] == pytest.approx(valid.median())
    assert len(valid) == 7


def test_implied_price_bridge(res):
    t = res["target"]
    med = res["summary"].loc["Median", "EV / EBITDA"]
    expected = (med * t["ebitda"] - t["total_debt"] + t["cash"]) / t["shares_out"]
    assert res["implied"].loc["EV / EBITDA", "Median"] == pytest.approx(expected)


def test_ranges_are_ordered(res):
    imp = res["implied"]
    assert (imp["25th Pct"] <= imp["Median"]).all()
    assert (imp["Median"] <= imp["75th Pct"]).all()


def test_requires_one_target(tmp_path):
    df = pd.read_csv(DATA)
    df["role"] = "peer"
    p = tmp_path / "no_target.csv"
    df.to_csv(p, index=False)
    with pytest.raises(ValueError):
        comps.run(p)
