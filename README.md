# The Evolution of NYC Open Data

A modernized replication of the 2014 study *"Structured Open Urban Data: Understanding the Landscape"* (Barbosa et al.), focusing on New York City's open data portal. We measure how the ecosystem has evolved in scale, quality, and integration potential using Jaccard similarity, the Lazo MinHash algorithm, and vector embeddings.

**Authors:** Ching-Yuan Peng, Jinu Hyun, Natiq Khan — NYU Center for Data Science

---

## Project Structure

```
3001-Data-Engineering/
│
├── scripts/
│   ├── crawl/                                  # Data acquisition
│   │   ├── nyc_socrata_datasets.py             #   Main crawler (Socrata SODA API)
│   │   ├── nyc_retry_failed.py                 #   Retry failed datasets
│   │   └── nyc_patch_cached_contents.py        #   Patch column-level statistics
│   │
│   └── analysis/                               # Analysis notebooks (in order)
│       ├── 01_dataset_landscape.ipynb          #   Phase 1 : Category distribution, quality metrics
│       ├── 02_embedding_column_joinability.ipynb  # Phase 2A: Column-level joinability via embeddings
│       ├── 03_embedding_schema_discovery.ipynb #   Phase 2B: Semantic schema clustering (cosine sim)
│       ├── 04_data_quality_schema.ipynb        #   Phase 2C: Data quality + schema independence
│       ├── 05_lazo_minhash_joinability.ipynb   #   Phase 2D: Lazo MinHash value-domain matching
│       ├── 06_evaluation_metrics.ipynb         #   Phase 3A: Precision / Recall / F1 per method
│       ├── 07_ground_truth_sampling.ipynb      #   Phase 3B: Stratified sampling + ground truth
│       └── 08_knowledge_graph.py               #   Phase 3C: Dataset connectivity knowledge graph
│
├── Data/                                       # Data files (not committed, see .gitignore)
│   ├── nyc_socrata_datasets.json               #   2,391 datasets with metadata + sample rows
│   ├── nyc_failed.json                         #   Datasets that failed to crawl
│   ├── jaccard_column_pairs.parquet            #   Jaccard column-pair candidates
│   ├── lazo_candidates.parquet                 #   Lazo containment candidates
│   ├── joinability_pairs_embedding.parquet     #   Embedding similarity pairs (dataset-level)
│   ├── joinability_pairs_embedding_column_level.parquet  # Embedding pairs (column-level)
│   ├── merged_column_pairs.parquet             #   All three methods merged
│   ├── ground_truth_candidates.csv             #   300-pair stratified ground truth (unlabeled)
│   ├── ground_truth_candidates - Desmond.csv   #   Desmond's labeled version
│   ├── joinability_graph.graphml               #   Full knowledge graph (GraphML)
│   ├── column_embeddings.npy                   #   Sentence embedding vectors
│   ├── column_names.json                       #   Column name index
│   ├── dataset_ids.json                        #   Dataset ID list
│   ├── data_hubs.csv                           #   Top hub datasets by weighted degree
│   └── wordlists/                              #   English wordlists for filtering
│
├── figures/                                    # Output figures for report
│   ├── 1_2_category_distribution.png           #   2026 category bar chart
│   ├── 1_2b_category_comparison_2014_2026.png  #   2014 vs 2026 category shift
│   ├── 1_3_tabular_nontabular.png              #   Tabular vs non-tabular breakdown
│   ├── 1_4_schema_size.png                     #   Schema size distribution
│   ├── 1_5_age_update_frequency.png            #   Dataset age and update frequency
│   ├── 1_6_popularity.png                      #   View count distribution
│   ├── 3_4_schema_independence.png             #   46% (2014) vs 91% (2026) stacked bar
│   ├── f1_by_group.png                         #   F1 by confidence stratum and method
│   ├── pr_scatter_overall.png                  #   Precision-Recall scatter
│   ├── knowledge_graph.png                     #   Full dataset connectivity graph
│   └── degree_distribution.png                #   Node degree distribution
│
├── Data_Engineering_Final_Project.pdf          # Written report (Overleaf export)
├── 2014-structured-open-urban-data-understanding-the-landscape.pdf  # Reference paper
├── project_proposal.md                         # Initial project proposal
├── WORKPLAN_EN.md                              # Task assignment (English)
└── requirements.txt                            # Python dependencies
```

---

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Data Acquisition

```bash
# Optional: set Socrata App Token to avoid rate limiting
export SOCRATA_APP_TOKEN="your_token_here"

python scripts/crawl/nyc_socrata_datasets.py       # Crawl all datasets
python scripts/crawl/nyc_retry_failed.py           # Retry failures
python scripts/crawl/nyc_patch_cached_contents.py  # Patch column stats
```

---

## Reproducing Results

Run notebooks in order from `01` to `08`. Each notebook reads from `Data/` and writes back to `Data/` or `figures/`.

| Notebook | Output |
|----------|--------|
| `01_dataset_landscape` | Landscape figures → `figures/1_*` |
| `02_embedding_column_joinability` | `joinability_pairs_embedding_column_level.parquet` |
| `03_embedding_schema_discovery` | `column_embeddings.npy`, `column_names.json` |
| `04_data_quality_schema` | Quality metrics, `figures/3_4_schema_independence.png` |
| `05_lazo_minhash_joinability` | `lazo_candidates.parquet` |
| `06_evaluation_metrics` | Precision / Recall / F1 tables and figures |
| `07_ground_truth_sampling` | `ground_truth_candidates.csv`, `figures/f1_by_group.png` |
| `08_knowledge_graph` | `joinability_graph.graphml`, `figures/knowledge_graph.png` |

---

## Key Findings (2014 → 2026)

| Metric | 2014 | 2026 |
|--------|------|------|
| Dataset count | 2,411 | 2,391 |
| Tabular datasets | 75% | 88% |
| Never-modified datasets | 70% | 60% |
| Schema independence rate (Jaccard = 1.0) | 46% | 91% |
| Top category | Social Services | City Government |

**Joinability detection (F1 on 300-pair ground truth):**

| Method | Precision | Recall | F1 |
|--------|-----------|--------|----|
| Jaccard (word-level) | 0.68 | 0.68 | 0.68 |
| Lazo (MinHash) | 0.92 | 0.90 | 0.90 |
| Embedding (cosine) | 0.67 | 0.67 | 0.67 |

---

## References

- Barbosa, L., Pham, K., Silva, C., Vieira, M. R., & Freire, J. (2014). Structured Open Urban Data: Understanding the Landscape. *Big Data*, 2(3), 144–154.
- Fernandez, R. C., Min, J., Nuno, D., & Madden, S. (2019). Lazo: A cardinality-based method for coupled estimation of Jaccard similarity and containment. *ICDE*.
