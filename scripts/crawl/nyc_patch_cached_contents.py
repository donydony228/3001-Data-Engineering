"""Patch cachedContents: re-fetch Views API to add column-level statistics to nyc_socrata_datasets.json"""
import requests
import json
import time
import os

APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN", "")
DOMAIN = "data.cityofnewyork.us"
TIMEOUT = 30

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
MAIN_FILE = os.path.join(DATA_DIR, "nyc_socrata_datasets.json")
FAILED_FILE = os.path.join(DATA_DIR, "nyc_patch_failed.json")


def get_metadata(dataset_id):
    url = f"https://{DOMAIN}/api/views/{dataset_id}.json"
    headers = {"X-App-Token": APP_TOKEN} if APP_TOKEN else {}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def main():
    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        datasets = json.load(f)

    total = len(datasets)
    patched = 0
    skipped = 0
    failed = []

    for i, entry in enumerate(datasets):
        dataset_id = entry["id"]
        name = entry["name"]

        # Skip if already has cachedContents
        if entry.get("full_metadata") and entry["full_metadata"].get("column_details"):
            first_col = entry["full_metadata"]["column_details"][0] if entry["full_metadata"]["column_details"] else {}
            if "cachedContents" in first_col:
                skipped += 1
                continue

        print(f"[{i+1}/{total}] {name}")

        try:
            meta = get_metadata(dataset_id)
            column_details = [
                {
                    "name": c.get("name"),
                    "type": c.get("dataTypeName"),
                    "cachedContents": c.get("cachedContents"),
                }
                for c in meta.get("columns", [])
            ]

            if entry.get("full_metadata"):
                entry["full_metadata"]["column_details"] = column_details
            else:
                entry["full_metadata"] = {
                    "category": meta.get("category"),
                    "attribution": meta.get("attribution"),
                    "license": meta.get("license", {}).get("name") if isinstance(meta.get("license"), dict) else meta.get("license"),
                    "rows_updated_at": meta.get("rowsUpdatedAt"),
                    "download_count": meta.get("downloadCount"),
                    "column_details": column_details,
                }

            patched += 1
            print(f"  OK: {len(column_details)} columns patched")
        except Exception as e:
            print(f"  FAIL: {e}")
            failed.append({"id": dataset_id, "name": name, "error": str(e)})

        time.sleep(0.3)

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(datasets, f, ensure_ascii=False, indent=2)

    with open(FAILED_FILE, "w", encoding="utf-8") as f:
        json.dump(failed, f, ensure_ascii=False, indent=2)

    print(f"\n=== Patch Complete ===")
    print(f"  Patched: {patched}")
    print(f"  Skipped (already has data): {skipped}")
    print(f"  Failed: {len(failed)}")


if __name__ == "__main__":
    main()
