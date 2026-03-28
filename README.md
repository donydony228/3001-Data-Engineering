# The Evolution of NYC Open Data — Tracking a Decade of Change

A modernized replication of the 2014 study *"Structured Open Urban Data: Understanding the Landscape"* (Barbosa et al.), focusing on New York City's open data portal. We use LLMs, vector embeddings, and the Lazo algorithm to quantify the evolution of data scale, quality, and integration potential over the past decade.

## Project Structure

```
3001-Data-Engineering/
├── data/                                 # Raw crawled data (not committed)
│   ├── nyc_socrata_datasets.json         #   2,391 datasets with metadata + 100 sample rows
│   └── nyc_failed.json                   #   Failed dataset list
│
├── scripts/
│   ├── crawl/                            # Data acquisition scripts
│   │   ├── nyc_socrata_datasets.py       #   Main crawler (Socrata Discovery + SODA + Views API)
│   │   ├── nyc_retry_failed.py           #   Retry failed datasets with longer timeout
│   │   └── nyc_patch_cached_contents.py  #   Patch column-level statistics (cachedContents)
│   │
│   └── analysis/                         # Analysis notebooks (Phase 1-3)
│       ├── 01_basic_statistics.ipynb     #   Phase 1: Basic statistics (all members)
│       ├── 02_semantic_discovery.ipynb   #   Phase 2: Semantic schema clustering (Member A)
│       ├── 03_quality_schema.ipynb       #   Phase 2: Data quality & HAC clustering (Member B)
│       └── 04_joinability.ipynb          #   Phase 2: Lazo & LLM schema mapping (Member C)
│
├── project_proposal.md                   # Project proposal
├── WORKPLAN.md                           # Workplan & task assignment (Chinese)
├── WORKPLAN_EN.md                        # Workplan & task assignment (English)
├── requirements.txt                      # Python dependencies
└── 2014-structured-open-urban-data-understanding-the-landscape.pdf  # Reference paper
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Data Acquisition

```bash
# Optional: set Socrata App Token to avoid rate limiting
export SOCRATA_APP_TOKEN="your_token_here"

# Crawl all NYC datasets (metadata + 100 sample rows each)
python scripts/crawl/nyc_socrata_datasets.py

# Retry any failed datasets with longer timeout
python scripts/crawl/nyc_retry_failed.py

# Patch column-level statistics (cachedContents)
python scripts/crawl/nyc_patch_cached_contents.py
```

## Key 2014 Baseline Numbers (NYC)

| Metric | 2014 Value | 2026 Value | Source |
|---|---|---|---|
| Dataset count | 2,411 | 2,391 | Table 1 |
| Schema independence (similarity=1) | 46% | TBD | Figure 10 |
| Schema variation across similarity levels | 26% | TBD | Figure 10 |
| Lat/Lon presence (all cities) | 52.9% | TBD | Figure 12 |
| Tables with date info | 40.4% | TBD | Figure 12 |
| Tables never modified (30 days) | 71% | TBD | Figure 8 |
| Table sparseness 0-0.1 (low null) | 63% | TBD | Figure 13 |

## References

- Barbosa, L., Pham, K., Silva, C., Vieira, M. R., & Freire, J. (2014). Structured Open Urban Data: Understanding the Landscape. *Big Data*, 2(3), 144-154.
- Original study code: https://github.com/ViDA-NYU/urban-data-study
