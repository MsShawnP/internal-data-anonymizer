"""Client-mode CLI tests: engagement.yml + tolerant intake + provenance report.

Skipped cleanly if the shared lailara_engagement library isn't installed, so the
core suite still runs in a bare environment.
"""

import pandas as pd
import pytest

pytest.importorskip("lailara_engagement")

from app import client_mode  # noqa: E402

_CONFIG = """
client:
  name: Meridian Farms
engagement:
  id: MER-2026-08
as_of_date: 2026-07-31
demo: true
anonymize:
  seed: 7
  types:
    retailer: company
  strategies:
    ssn: hash
"""

_CSV = (
    "order_date,ship_zip,customer_name,retailer,ssn,amount\n"
    "2024-03-15,02134,John Smith,Harvest Market,123-45-6789,100.50\n"
    "03/20/2024,08079,Jane Doe,Fresh Fields,234-56-7890,200.00\n"
    "2024-04-01,10001,Maria Garcia,Green Basket,345-67-8901,300.25\n"
    "2024-05-10,60601,Bob Jones,Valley Foods,456-78-9012,50.00\n"
)


@pytest.fixture
def engagement(tmp_path):
    cfg = tmp_path / "engagement.demo.yml"
    cfg.write_text(_CONFIG, encoding="utf-8")
    src = tmp_path / "sample.csv"
    src.write_text(_CSV, encoding="utf-8")
    out = tmp_path / "client-output"
    return str(cfg), str(src), str(out)


def test_run_produces_output_and_report(engagement):
    cfg, src, out = engagement
    result = client_mode.run(cfg, src, out, fmt="csv")
    assert result["rows"] == 4
    import os
    assert os.path.isfile(result["output"])
    assert os.path.isfile(result["report"])


def test_no_original_values_leak(engagement):
    cfg, src, out = engagement
    result = client_mode.run(cfg, src, out)
    df = pd.read_csv(result["output"], dtype=str)
    text = df.to_csv(index=False)
    # None of the original sensitive values survive
    for leaked in ["John Smith", "Jane Doe", "123-45-6789", "456-78-9012"]:
        assert leaked not in text


def test_zip_leading_zeros_preserved(engagement):
    cfg, src, out = engagement
    result = client_mode.run(cfg, src, out)
    df = pd.read_csv(result["output"], dtype=str)
    for z in df["ship_zip"]:
        assert len(z) == 5 and z.isdigit()  # no "8079.0", leading zeros intact


def test_dates_changed(engagement):
    cfg, src, out = engagement
    result = client_mode.run(cfg, src, out)
    df = pd.read_csv(result["output"], dtype=str)
    original = ["2024-03-15", "03/20/2024", "2024-04-01", "2024-05-10"]
    assert all(df["order_date"].iloc[i] != original[i] for i in range(4))


def test_config_overrides_applied(engagement):
    cfg, src, out = engagement
    result = client_mode.run(cfg, src, out)
    plans = {p.name: p for p in result["plans"]}
    assert plans["ssn"].strategy == "hash"       # strategy override
    assert plans["retailer"].detected_type == "company"  # type override


def test_report_is_branded_and_provenance_footed(engagement):
    cfg, src, out = engagement
    result = client_mode.run(cfg, src, out, final=False)
    html = open(result["report"], encoding="utf-8").read()
    assert "Meridian Farms" in html
    assert "#f5f3ee" in html            # warm canvas
    assert "DRAFT" in html              # watermark until --final
    assert "SHA-256" in html            # provenance footer
    assert "Anonymization Report" in html


def test_final_drops_watermark(engagement):
    cfg, src, out = engagement
    result = client_mode.run(cfg, src, out, final=True)
    html = open(result["report"], encoding="utf-8").read()
    assert "ll-draft" not in html
