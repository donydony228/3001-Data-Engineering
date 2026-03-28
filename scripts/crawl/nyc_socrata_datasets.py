import requests
import json
import time
import os

APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN", "")

DOMAIN = "data.cityofnewyork.us"
CATALOG_URL = "https://api.us.socrata.com/api/catalog/v1"
LIMIT = 100


def get_all_nyc_datasets():
    """Through Discovery API get all NYC Socrata datasets"""
    all_results = []
    offset = 0

    while True:
        params = {
            "domains": DOMAIN,
            "only": "datasets",
            "limit": LIMIT,
            "offset": offset,
        }
        resp = requests.get(CATALOG_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        total = data.get("resultSetSize", 0)
        all_results.extend(results)

        print(f"Retrieved {len(all_results)} / {total} records")

        if len(all_results) >= total or not results:
            break
        offset += LIMIT
        time.sleep(0.5)

    return all_results


def get_metadata(dataset_id):
    """Get detailed metadata for a single dataset"""
    url = f"https://{DOMAIN}/api/views/{dataset_id}.json"
    headers = {}
    if APP_TOKEN:
        headers["X-App-Token"] = APP_TOKEN
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_sample_rows(dataset_id, n=100):
    """Get sample rows from a dataset"""
    url = f"https://{DOMAIN}/resource/{dataset_id}.json"
    params = {"$limit": n}
    if APP_TOKEN:
        params["$$app_token"] = APP_TOKEN
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def main():
    print(f"=== Retrieve all datasets from {DOMAIN} ===")
    datasets = get_all_nyc_datasets()
    print(f"Found {len(datasets)} datasets\n")

    results = []
    failed = []

    for i, ds in enumerate(datasets):
        resource = ds.get("resource", {})
        name = resource.get("name", "N/A")
        dataset_id = resource.get("id", "")
        description = resource.get("description", "")[:200]
        columns = resource.get("columns_field_name", [])

        print(f"[{i+1}/{len(datasets)}] {name}")
        print(f"  ID: {dataset_id} | Columns: {len(columns)}")

        entry = {
            "name": name,
            "id": dataset_id,
            "domain": DOMAIN,
            "description": description,
            "columns": columns,
            "permalink": ds.get("permalink", ""),
        }

        errors = []

        # Get detailed metadata
        try:
            meta = get_metadata(dataset_id)
            entry["full_metadata"] = {
                "category": meta.get("category"),
                "attribution": meta.get("attribution"),
                "license": meta.get("license", {}).get("name") if isinstance(meta.get("license"), dict) else meta.get("license"),
                "rows_updated_at": meta.get("rowsUpdatedAt"),
                "download_count": meta.get("downloadCount"),
                "column_details": [
                    {
                        "name": c.get("name"),
                        "type": c.get("dataTypeName"),
                        "cachedContents": c.get("cachedContents"),
                    }
                    for c in meta.get("columns", [])
                ],
            }
        except Exception as e:
            print(f"  Warning: Failed to retrieve metadata: {e}")
            entry["full_metadata"] = None
            errors.append({"type": "metadata", "error": str(e)})

        # Get sample rows
        try:
            sample = get_sample_rows(dataset_id, n=100)
            entry["sample_rows"] = sample
            print(f"  OK: Retrieved {len(sample)} sample rows")
        except Exception as e:
            print(f"  Warning: Failed to retrieve sample rows: {e}")
            entry["sample_rows"] = None
            errors.append({"type": "sample_rows", "error": str(e)})

        if errors:
            failed.append({"id": dataset_id, "name": name, "errors": errors})

        results.append(entry)
        time.sleep(0.3)

    # Save results
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "nyc_socrata_datasets.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Save failed list
    failed_file = os.path.join(output_dir, "nyc_failed.json")
    with open(failed_file, "w", encoding="utf-8") as f:
        json.dump(failed, f, ensure_ascii=False, indent=2)

    print(f"\n=== Retry Complete ===")
    print(f"  Success: {len(results) - len(failed)} / {len(results)}")
    print(f"  Still Failed: {len(failed)} (List saved to {failed_file})")


if __name__ == "__main__":
    main()
