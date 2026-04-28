# Country Expansion Design Spec

**Date:** 2026-04-27
**Feature:** Expand JV country coverage from 3 to 6 countries, anchored to real SKX 10-K data

---

## Goal

Replace the simulated JV country set with the actual Skechers joint venture countries disclosed in the SKX FY2024 10-K (SEC Accession: 0000950170-25-030016). Remove Japan (a wholly-owned subsidiary, not a JV) and add China, Malaysia, Singapore, and Thailand — all confirmed JV markets in the filing.

---

## Background

Skechers U.S.A., Inc. (NYSE: SKX) is publicly traded. The FY2024 10-K explicitly lists JV ownership stakes:

> "Our joint venture interests include China, Malaysia, Vietnam and Singapore (50%), Thailand (51%), Mexico (60%), South Korea (65%) and Israel (75%)."

Japan is a wholly-owned subsidiary. The prior dashboard included Japan and used Wolverine World Wide as a proxy — both are now corrected using the real source.

**FY2024 Revenue by region (from SKX 10-K):**
| Region | Revenue |
|---|---|
| Americas (AMER) | $4,367.9M |
| EMEA | $2,224.4M |
| APAC | $2,377.1M |
| China (disclosed separately) | $1,218.2M |

---

## Countries

**Before:** Japan, Mexico, South Korea
**After:** China, Malaysia, Singapore, Thailand, Mexico, South Korea

Vietnam and Israel are valid JV countries but excluded to keep the dashboard focused on the largest markets in each region.

---

## Architecture

Single-file change to `data/simulate.py`:
- Remove `"Japan"` from `COUNTRIES`, add `"China"`, `"Malaysia"`, `"Singapore"`, `"Thailand"`
- Update `COUNTRY_REGION` with new mappings
- Update `COUNTRY_VOLUME` with calibrated values
- Replace `BENCHMARK_SOURCE` comment to cite SKX 10-K instead of Wolverine WWW

Two new tests added to `tests/test_simulate.py`. All 14 existing tests must continue to pass (16 total after expansion).

---

## COUNTRY_VOLUME Calibration

Normalized to **South Korea = 1.0** (estimated ~$300M, the largest non-China APAC JV).

| Country | JV % | Revenue Basis | COUNTRY_VOLUME |
|---|---|---|---|
| China | 50% | $1,218M actual (SKX 10-K) ÷ $300M baseline | 4.10 |
| South Korea | 65% | Baseline | 1.00 |
| Mexico | 60% | ~$290M est. from AMER international pool ÷ $300M | 0.96 |
| Malaysia | 50% | ~$144M est. from APAC ex-China pool ÷ $300M | 0.48 |
| Thailand | 51% | ~$126M est. from APAC ex-China pool ÷ $300M | 0.42 |
| Singapore | 50% | ~$90M est. city-state, smaller market ÷ $300M | 0.30 |

**What is real vs. estimated:**
- **Real:** China ($1,218M directly disclosed in 10-K)
- **Estimated:** South Korea, Mexico, Malaysia, Singapore, Thailand — derived by reasoning from the APAC ex-China pool ($1,159M) and AMER international pool (~$947M), with market-size priors (GDP, Skechers store presence). The BENCHMARK_SOURCE comment in simulate.py will document this distinction explicitly.

**APAC pool reasoning:**
- APAC total: $2,377M
- China: $1,218M (actual)
- APAC ex-China: $1,159M (shared across Japan subsidiary + South Korea + Malaysia + Singapore + Thailand)
- Japan subsidiary estimated at ~$500M (large market, wholly owned)
- Remaining JV pool: ~$659M split as South Korea $300M, Malaysia $144M, Thailand $126M, Singapore $90M

---

## COUNTRY_REGION Mapping

```python
COUNTRY_REGION = {
    "China":       "Asia Pacific",
    "Malaysia":    "Asia Pacific",
    "Singapore":   "Asia Pacific",
    "Thailand":    "Asia Pacific",
    "South Korea": "Asia Pacific",
    "Mexico":      "Latin America",
}
```

---

## Tests

```python
def test_country_list():
    """Dashboard should reflect actual Skechers JV countries."""
    from data.simulate import COUNTRIES
    assert "China" in COUNTRIES
    assert "Japan" not in COUNTRIES  # Japan is a subsidiary, not a JV
    assert len(COUNTRIES) == 6


def test_country_volume_china_largest():
    """China is the largest JV market by revenue ($1.22B actual from SKX 10-K)."""
    from data.simulate import COUNTRY_VOLUME
    assert COUNTRY_VOLUME["China"] == max(COUNTRY_VOLUME.values())
    assert 3.8 <= COUNTRY_VOLUME["China"] <= 4.5
    assert COUNTRY_VOLUME["South Korea"] == 1.0  # baseline
    assert COUNTRY_VOLUME["Singapore"] < COUNTRY_VOLUME["Malaysia"]  # city-state < larger market
```

---

## Files Changed

| File | Change |
|---|---|
| `data/simulate.py` | Update `BENCHMARK_SOURCE`, `COUNTRIES`, `COUNTRY_REGION`, `COUNTRY_VOLUME` |
| `tests/test_simulate.py` | Add `test_country_list`, `test_country_volume_china_largest` |
