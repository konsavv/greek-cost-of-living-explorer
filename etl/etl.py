"""
ETL for the Greek Cost-of-Living & Real Estate Explorer
--------------------------------------------------------
Produces ../public/data/economy.json which the Nuxt front-end reads.

Data sources (all official / open):
  1. INFLATION  -> Greek HICP annual inflation, Eurostat dataset `prc_hicp_aind`.
  2. REGIONAL INCOME -> REAL net disposable income of private households per
                        inhabitant (EUR_HAB), per Greek NUTS-2 region, Eurostat
                        dataset `nama_10r_2hhinc`. ELSTAT produces these figures
                        and publishes them through Eurostat (Greece has no
                        equivalent open REST API of its own).
  3. RENT       -> average monthly rent per region. NOTE: rent by region is NOT
                   an official statistic (it is private-market data). The values
                   here are INDICATIVE and clearly flagged; replace them with a
                   market source you trust (e.g. Spitogatos / XE market reports).

Affordability index = monthly rent (1BR) as % of monthly disposable income
per inhabitant (lower = more affordable).

Every network call falls back gracefully, so the app always builds even offline.

Run:  python etl.py
"""

import json
import os
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    requests = None

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "public", "data", "economy.json")

EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

# Greek NUTS-2 region codes -> display name + INDICATIVE rent (market data).
# rent_1br_eur / rent_2br_eur are indicative monthly rents — REPLACE with a
# real market source. income figures come from Eurostat at runtime (below);
# `income_fallback_eur` is used only when offline.
REGIONS = [
    {"code": "EL30", "region": "Attica (Athens)",                "rent_1br_eur": 620, "rent_2br_eur": 830, "income_fallback_eur": 15200},
    {"code": "EL52", "region": "Central Macedonia (Thessaloniki)", "rent_1br_eur": 430, "rent_2br_eur": 560, "income_fallback_eur": 12100},
    {"code": "EL43", "region": "Crete",                          "rent_1br_eur": 480, "rent_2br_eur": 640, "income_fallback_eur": 12600},
    {"code": "EL61", "region": "Thessaly",                       "rent_1br_eur": 350, "rent_2br_eur": 470, "income_fallback_eur": 11400},
    {"code": "EL63", "region": "Western Greece",                 "rent_1br_eur": 330, "rent_2br_eur": 440, "income_fallback_eur": 10800},
    {"code": "EL64", "region": "Central Greece",                 "rent_1br_eur": 340, "rent_2br_eur": 450, "income_fallback_eur": 12000},
    {"code": "EL42", "region": "South Aegean",                   "rent_1br_eur": 560, "rent_2br_eur": 760, "income_fallback_eur": 13900},
    {"code": "EL54", "region": "Epirus",                         "rent_1br_eur": 320, "rent_2br_eur": 430, "income_fallback_eur": 10900},
    {"code": "EL51", "region": "Eastern Macedonia & Thrace",     "rent_1br_eur": 300, "rent_2br_eur": 400, "income_fallback_eur": 10400},
    {"code": "EL65", "region": "Peloponnese",                    "rent_1br_eur": 360, "rent_2br_eur": 480, "income_fallback_eur": 11500},
    {"code": "EL41", "region": "North Aegean",                   "rent_1br_eur": 340, "rent_2br_eur": 450, "income_fallback_eur": 11000},
    {"code": "EL62", "region": "Ionian Islands",                 "rent_1br_eur": 420, "rent_2br_eur": 560, "income_fallback_eur": 12200},
    {"code": "EL53", "region": "Western Macedonia",              "rent_1br_eur": 310, "rent_2br_eur": 410, "income_fallback_eur": 11300},
]

FALLBACK_INFLATION = [
    {"year": 2016, "hicp": 0.0}, {"year": 2017, "hicp": 1.1},
    {"year": 2018, "hicp": 0.8}, {"year": 2019, "hicp": 0.5},
    {"year": 2020, "hicp": -1.3}, {"year": 2021, "hicp": 0.6},
    {"year": 2022, "hicp": 9.3}, {"year": 2023, "hicp": 4.2},
    {"year": 2024, "hicp": 3.0}, {"year": 2025, "hicp": 2.6},
]


# ---------------------------------------------------------------------------
# JSON-stat helper: Eurostat returns values as a flat, row-major index over the
# dataset's dimensions. This turns a flat index back into per-dimension coords.
# ---------------------------------------------------------------------------
def unflatten(flat_index, sizes):
    coords = []
    for size in reversed(sizes):
        coords.append(flat_index % size)
        flat_index //= size
    return list(reversed(coords))


def get_json(url):
    if requests is None:
        raise RuntimeError("`requests` not installed")
    r = requests.get(url, timeout=30, headers={"User-Agent": "gcole-etl/1.0"})
    r.raise_for_status()
    return r.json()


def fetch_inflation():
    """Greek HICP annual average inflation (real). Falls back if offline."""
    url = f"{EUROSTAT}/prc_hicp_aind?format=JSON&coicop=CP00&unit=RCH_A_AVG&geo=EL"
    try:
        js = get_json(url)
        idx_to_year = {v: k for k, v in js["dimension"]["time"]["category"]["index"].items()}
        rows = [
            {"year": int(idx_to_year[int(i)]), "hicp": round(float(v), 1)}
            for i, v in js["value"].items()
            if int(i) in idx_to_year
        ]
        rows.sort(key=lambda x: x["year"])
        if not rows:
            raise ValueError("empty response")
        return rows, "Eurostat prc_hicp_aind (live)"
    except Exception as e:  # noqa: BLE001
        print(f"[etl] inflation live fetch failed ({e}); using fallback.")
        return FALLBACK_INFLATION, "bundled fallback (offline)"


def fetch_regional_income():
    """
    Real disposable income per inhabitant for each Greek NUTS-2 region
    (Eurostat tgs00026). Returns {geo_code: {"value": float, "year": int,
    "unit": str}}. Self-discovers the per-inhabitant unit so we don't depend on
    a hard-coded unit code. Falls back to {} if offline.
    """
    # nama_10r_2hhinc gives income PER INHABITANT (EUR_HAB). We pin that unit so
    # we never accidentally read a regional TOTAL (e.g. tgs00026 only offers
    # "million PPS", which would make the affordability ratio meaningless).
    UNIT = "EUR_HAB"
    geo_params = "".join(f"&geo={r['code']}" for r in REGIONS)
    url = (f"{EUROSTAT}/nama_10r_2hhinc?format=JSON"
           f"&freq=A&unit={UNIT}&direct=BAL&na_item=B6N{geo_params}")
    try:
        js = get_json(url)
        dims, sizes = js["id"], js["size"]
        geo_idx = js["dimension"]["geo"]["category"]["index"]
        time_idx = js["dimension"]["time"]["category"]["index"]

        # Safety: the response's unit dimension must be the per-inhabitant one.
        unit_codes = list(js["dimension"]["unit"]["category"]["index"])
        if not any("HAB" in u.upper() for u in unit_codes):
            raise ValueError(f"no per-inhabitant unit in response ({unit_codes})")

        p_geo, p_time = dims.index("geo"), dims.index("time")
        idx2geo = {v: k for k, v in geo_idx.items()}
        idx2year = {v: k for k, v in time_idx.items()}

        best = {}  # geo -> (year, value)
        for flat, val in js["value"].items():
            if val is None:
                continue
            coords = unflatten(int(flat), sizes)
            g = idx2geo.get(coords[p_geo])
            y = int(idx2year.get(coords[p_time], 0))
            # Sanity: annual disposable income per inhabitant is realistically
            # a few thousand to a few tens of thousands of euros. Anything wildly
            # outside that means we grabbed the wrong measure -> reject.
            if g and 2000 <= float(val) <= 60000:
                if g not in best or y > best[g][0]:
                    best[g] = (y, float(val))

        if not best:
            raise ValueError("empty income response")
        return {g: {"value": v, "year": y, "unit": UNIT} for g, (y, v) in best.items()}, \
               f"Eurostat nama_10r_2hhinc (live, {UNIT})"
    except Exception as e:  # noqa: BLE001
        print(f"[etl] regional income live fetch failed ({e}); using fallback.")
        return {}, "bundled fallback (offline)"


def build_regions(income_map):
    rows = []
    for r in REGIONS:
        live = income_map.get(r["code"])
        if live:
            income_year = round(live["value"])
            income_is_real = True
            income_year_ref = live["year"]
        else:
            income_year = r["income_fallback_eur"]
            income_is_real = False
            income_year_ref = None

        income_month = round(income_year / 12)
        affordability = round(r["rent_1br_eur"] / income_month * 100, 1)

        rows.append({
            "region": r["region"],
            "code": r["code"],
            "income_year_eur": income_year,
            "income_month_eur": income_month,
            "income_is_real": income_is_real,
            "income_year_ref": income_year_ref,
            "rent_1br_eur": r["rent_1br_eur"],
            "rent_2br_eur": r["rent_2br_eur"],
            "affordability_pct": affordability,
        })
    rows.sort(key=lambda x: x["affordability_pct"])
    return rows


def main():
    inflation, inflation_source = fetch_inflation()
    inflation = inflation[-15:]  # keep the last 15 years for a readable chart
    income_map, income_source = fetch_regional_income()
    regions = build_regions(income_map)
    n_real = sum(1 for r in regions if r["income_is_real"])

    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "inflation_source": inflation_source,
            "income_source": income_source,
            "income_real_count": n_real,
            "rent_source": "INDICATIVE market data — replace with a real source (e.g. Spitogatos / XE reports)",
            "note": "Affordability = 1BR monthly rent as % of monthly disposable income per inhabitant (lower is more affordable).",
        },
        "regions": regions,
        "inflation": inflation,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[etl] wrote {OUT}")
    print(f"[etl] inflation: {inflation_source} ({len(inflation)} yrs)")
    print(f"[etl] income: {income_source}  ({n_real}/{len(regions)} regions with live data)")


if __name__ == "__main__":
    main()
