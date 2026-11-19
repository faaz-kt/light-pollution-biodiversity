"""
Step 1b: request and download the FULL bird dataset for one state from GBIF
(Karnataka = main study; Kerala = replication, see PLAN_step8_kerala.md).

How a GBIF download works:
  1. We send GBIF a "request" describing which records we want (the filters below).
  2. GBIF's servers build a zip file. For millions of records this takes from
     ~15 minutes to a few hours. GBIF also emails you when it's ready.
  3. We download the zip. GBIF gives every download a DOI (a permanent citation
     link), so anyone can get exactly the same data later. You MUST cite this DOI
     in any write-up: that's GBIF's rule, and it makes your work reproducible.

You need a GBIF account (free, gbif.org). The script asks for your username and
password when it runs. They are only sent to GBIF, never saved.

The script is restart-safe: the download key is saved in bigdata/<folder>/raw/, so if you
stop it while GBIF is still working, just run it again and it carries on.

Run:  python step1b_gbif_download.py
"""

import getpass
import json
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------- SETTINGS --
REGION = "karnataka"        # "karnataka" (main study), "kerala" (replication) or "india" (PLAN_india.md)
REGIONS = {"karnataka": {"folder": "lpb", "gadm": "IND.16_1"},
           "kerala": {"folder": "lpb_kerala", "gadm": "IND.17_1"},
           "india": {"folder": "lpb_india", "gadm": "IND"}}      # all of India (GADM level 0), ~50 M records
API = "https://api.gbif.org/v1/occurrence/download"
REGION_GID = REGIONS[REGION]["gadm"]    # GADM code of the state
# Birds, in the Catalogue of Life taxonomy GBIF switched to in 2026 (Aves = "V2" in that checklist).
# The Karnataka download (DOI 10.15468/dl.t3hgj6) used exactly this, so Kerala must too.
COL_CHECKLIST = "7ddf754f-d193-4cc9-b351-99906754a03b"
TAXON_KEY = "V2"
YEAR_FROM, YEAR_TO = 2015, 2025   # before 2015 there are few records; 2026 is still incomplete
FORMAT = "SIMPLE_CSV"       # one tab-separated table, ~50 columns
CHECK_EVERY = 60            # seconds between "is it ready yet?" checks
WAIT = True                 # False = just send the request and stop; run again later to download
KNOWN_KEY = None            # a download you requested on gbif.org yourself, e.g. "0013799-261110092616502"

import sys
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    BASE = Path("/content/drive/MyDrive/bigdata") / REGIONS[REGION]["folder"]
else:
    # Laptop: the data folder can be C:\Users\<you>\bigdata\<folder> or Downloads\bigdata\<folder> (first found).
    _options = [Path.home() / "bigdata" / REGIONS[REGION]["folder"],
                Path.home() / "Downloads" / "bigdata" / REGIONS[REGION]["folder"]]
    BASE = next((p for p in _options if p.exists()), _options[0])
RAW = BASE / "raw"
RAW.mkdir(parents=True, exist_ok=True)
KEY_FILE = RAW / "gbif_download_key.txt"      # remembers our request between runs
INFO_FILE = RAW / "gbif_download_info.json"   # DOI, record count, size, filters
if KNOWN_KEY:
    KEY_FILE.write_text(KNOWN_KEY)               # use that download instead of sending a new request

# The filters, in GBIF's "predicate" language. "and" = all of them must be true.
PREDICATE = {
    "type": "and",
    "predicates": [
        {"type": "in", "key": "GADM_GID", "values": [REGION_GID]},
        {"type": "in", "key": "TAXON_KEY", "values": [TAXON_KEY], "checklistKey": COL_CHECKLIST},
        {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},           # must have a location
        {"type": "equals", "key": "HAS_GEOSPATIAL_ISSUE", "value": "false"},    # GBIF found no location problems
        {"type": "greaterThanOrEquals", "key": "YEAR", "value": str(YEAR_FROM)},
        {"type": "lessThanOrEquals", "key": "YEAR", "value": str(YEAR_TO)},
    ],
}


def request_download():
    """Ask GBIF to prepare the download. Returns the download key (an ID like 0012345-261115...)."""
    print("GBIF login (only sent to GBIF, not saved)")
    user = input("  username: ").strip()
    password = getpass.getpass("  password (typing is hidden): ")
    body = {"creator": user, "sendNotification": True, "format": FORMAT, "checklistKey": COL_CHECKLIST,
            "predicate": PREDICATE}
    r = requests.post(f"{API}/request", json=body, auth=(user, password), timeout=60)
    if r.status_code == 401:
        raise SystemExit("GBIF says the username or password is wrong (or the account isn't confirmed yet).")
    r.raise_for_status()
    key = r.text.strip()
    KEY_FILE.write_text(key)
    print(f"Request accepted. Download key: {key}")
    print(f"You can also watch it here: https://www.gbif.org/occurrence/download/{key}")
    return key


def wait_until_ready(key):
    """Check every CHECK_EVERY seconds until GBIF has finished building the file."""
    while True:
        info = requests.get(f"{API}/{key}", timeout=60).json()
        status = info["status"]
        if status == "SUCCEEDED":
            return info
        if status in ("KILLED", "CANCELLED", "FAILED"):
            KEY_FILE.unlink()   # so the next run sends a fresh request
            raise SystemExit(f"GBIF stopped the download ({status}). Run the script again to retry.")
        print(f"  {time.strftime('%H:%M')}  status: {status} (GBIF is still preparing it; Ctrl+C is safe)")
        time.sleep(CHECK_EVERY)


def download_file(info):
    """Save the zip into the raw/ folder, showing progress. Skips it if already complete."""
    target = RAW / f"gbif_{info['key']}.zip"
    size = info.get("size", 0)
    if target.exists() and target.stat().st_size == size:
        print(f"Already downloaded: {target.name}")
        return target
    print(f"Downloading {size / 1e9:.2f} GB to {target} ...")
    with requests.get(info["downloadLink"], stream=True, timeout=120) as r:
        r.raise_for_status()
        done = 0
        with open(target, "wb") as f:
            for chunk in r.iter_content(chunk_size=8 * 1024 * 1024):   # 8 MB at a time
                f.write(chunk)
                done += len(chunk)
                print(f"\r  {done / 1e9:.2f} / {size / 1e9:.2f} GB", end="")
    print()
    return target


key = KEY_FILE.read_text().strip() if KEY_FILE.exists() else request_download()
status = requests.get(f"{API}/{key}", timeout=60).json()["status"]
if status != "SUCCEEDED" and not WAIT:
    print(f"GBIF status: {status}. GBIF emails you when it's ready; then run this script again "
          f"(it remembers the request) to download.")
else:
    print(f"Waiting for download {key} ...")
    info = wait_until_ready(key)

    # Save the important facts, above all the DOI for citing.
    summary = {
        "key": info["key"],
        "doi": info.get("doi"),
        "cite_as": f"GBIF.org ({info.get('created', '')[:10]}) GBIF Occurrence Download https://doi.org/{info.get('doi')}",
        "records": info.get("totalRecords"),
        "size_bytes": info.get("size"),
        "created": info.get("created"),
        "region": REGION,
        "taxonomy_checklist": COL_CHECKLIST,
        "filters": PREDICATE,
    }
    INFO_FILE.write_text(json.dumps(summary, indent=2))
    print(f"Ready: {summary['records']:,} records, DOI {summary['doi']}")

    zip_path = download_file(info)
    print(f"Done. Data: {zip_path}")
    print(f"Citation: {summary['cite_as']}")
    print("Don't unzip it by hand: the next step reads it in pieces, straight from the zip.")
