"""
live_nav_fetch.py
Bluestock Mutual Fund Analytics — Day 1
Fetches live NAV data from mfapi.in for 6 key schemes.
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime

RAW_DIR = "data/raw"
BASE_URL = "https://api.mfapi.in/mf"

SCHEMES = {
    125497: "HDFC Top 100 Direct",
    119551: "SBI Bluechip Direct",
    120503: "ICICI Prudential Bluechip Direct",
    118632: "Nippon India Large Cap Direct",
    119092: "Axis Bluechip Direct",
    120841: "Kotak Bluechip Direct",
}


def fetch_nav(amfi_code: int, scheme_name: str) -> pd.DataFrame | None:
    """Fetch NAV history for a given AMFI code from mfapi.in."""
    url = f"{BASE_URL}/{amfi_code}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        meta = data.get("meta", {})
        nav_data = data.get("data", [])

        print(f"\n  ✅ {scheme_name} (AMFI: {amfi_code})")
        print(f"     Fund House : {meta.get('fund_house', 'N/A')}")
        print(f"     Scheme     : {meta.get('scheme_name', 'N/A')}")
        print(f"     Category   : {meta.get('scheme_category', 'N/A')}")
        print(f"     NAV records: {len(nav_data)}")

        if nav_data:
            df = pd.DataFrame(nav_data)
            df["amfi_code"] = amfi_code
            df["scheme_name"] = scheme_name
            df["fetched_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Latest NAV
            latest = nav_data[0]
            print(f"     Latest NAV : ₹{latest['nav']} on {latest['date']}")
            return df

    except requests.exceptions.ConnectionError:
        print(f"\n  ⚠  {scheme_name} (AMFI: {amfi_code}) — Network unavailable; using cached stub.")
        # Return a minimal stub so the pipeline continues offline
        stub = pd.DataFrame([{
            "date": datetime.now().strftime("%d-%m-%Y"),
            "nav": "N/A",
            "amfi_code": amfi_code,
            "scheme_name": scheme_name,
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }])
        return stub
    except Exception as e:
        print(f"\n  ❌ Failed to fetch {scheme_name}: {e}")
        return None


def main():
    print("=" * 60)
    print("  BLUESTOCK MF — LIVE NAV FETCH (mfapi.in)")
    print(f"  Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_dfs = []
    for amfi_code, scheme_name in SCHEMES.items():
        df = fetch_nav(amfi_code, scheme_name)
        if df is not None:
            all_dfs.append(df)

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        out_path = os.path.join(RAW_DIR, "live_nav_data.csv")
        combined.to_csv(out_path, index=False)
        print(f"\n  💾 Saved {len(combined):,} records → {out_path}")
    else:
        print("\n  ❌ No data fetched.")

    print("=" * 60)


if __name__ == "__main__":
    main()
