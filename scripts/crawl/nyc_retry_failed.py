"""Retry failed datasets"""
import requests
import json
import time
import os

APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN", "")
DOMAIN = "data.cityofnewyork.us"
TIMEOUT = 60  

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
FAILED_FILE = os.path.join(DATA_DIR, "nyc_failed.json")
MAIN_FILE = os.path.join(DATA_DIR, "nyc_socrata_datasets.json")


def get_metadata(dataset_id):
    url = f"https://{DOMAIN}/api/views/{dataset_id}.json"
    headers = {"X-App-Token": APP_TOKEN} if APP_TOKEN else {}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_sample_rows(dataset_id, n=100):
    url = f"https://{DOMAIN}/resource/{dataset_id}.json"
    params = {"$limit": n}
    if APP_TOKEN:
        params["$$app_token"] = APP_TOKEN
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def main():
    with open(FAILED_FILE, "r", encoding="utf-8") as f:
        failed_list = json.load(f)

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        main_data = json.load(f)

    # Create id -> index mapping
    id_to_index = {entry["id"]: i for i, entry in enumerate(main_data)}

    still_failed = []

    for item in failed_list:
        dataset_id = item["id"]
        name = item["name"]
        error_types = [e["type"] for e in item["errors"]]

        print(f"Retrying: {name} (ID: {dataset_id})")
        print(f"  Needs: {', '.join(error_types)}")

        idx = id_to_index.get(dataset_id)
        if idx is None:
            print(f"  Skip: Not found in main dataset")
            still_failed.append(item)
            continue

        remaining_errors = []

        if "metadata" in error_types:
            try:
                meta = get_metadata(dataset_id)
                main_data[idx]["full_metadata"] = {
                    "category": meta.get("category"),
                    "attribution": meta.get("attribution"),
                    "license": meta.get("license", {}).get("name") if isinstance(meta.get("license"), dict) else meta.get("license"),
                    "rows_updated_at": meta.get("rowsUpdatedAt"),
                    "download_count": meta.get("downloadCount"),
                    "column_details": [
                        {"name": c.get("name"), "type": c.get("dataTypeName")}
                        for c in meta.get("columns", [])
                    ],
                }
                print(f"  OK: metadata")
            except Exception as e:
                print(f"  FAIL: metadata - {e}")
                remaining_errors.append({"type": "metadata", "error": str(e)})

        if "sample_rows" in error_types:
            try:
                sample = get_sample_rows(dataset_id, n=100)
                main_data[idx]["sample_rows"] = sample
                print(f"  OK: sample_rows ({len(sample)} 列)")
            except Exception as e:
                print(f"  FAIL: sample_rows - {e}")
                remaining_errors.append({"type": "sample_rows", "error": str(e)})

        if remaining_errors:
            still_failed.append({"id": dataset_id, "name": name, "errors": remaining_errors})

        time.sleep(0.5)

    # Write back to main file
    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(main_data, f, ensure_ascii=False, indent=2)

    # Update failed list
    with open(FAILED_FILE, "w", encoding="utf-8") as f:
        json.dump(still_failed, f, ensure_ascii=False, indent=2)

    print(f"\n=== Retry Complete ===")
    print(f"  Success: {len(failed_list) - len(still_failed)} / {len(failed_list)}")
    print(f"  Still Failed: {len(still_failed)}")


if __name__ == "__main__":
    main()
