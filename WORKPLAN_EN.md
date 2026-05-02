# NYC Open Data Project — Workplan & Task Assignment

## Team: 3 members (A, B, C)

---

## Phase 1 — Common Foundation (Week 1)

> All three members work together to understand the data and produce shared baseline statistics.

### Tasks

| # | Task | Description | Output |
|---|---|---|---|
| 1.1 | Load & clean | Read `nyc_socrata_datasets.json` into pandas DataFrame | `nyc_metadata.csv` |
| 1.2 | Dataset count & category distribution | Count datasets per category, compare with paper Table 1 | Bar chart |
| 1.3 | Format proportions | Tabular vs non-tabular ratio, compare with paper Figure 2, 3 | Pie chart |
| 1.4 | Schema size distribution | Distribution of column counts per dataset, compare with paper Figure 9 | Histogram |
| 1.5 | Dataset age & update frequency | Analyze `createdAt` / `rowsUpdatedAt` distributions | Histogram |
| 1.6 | Popularity distribution | Download count / view count distributions, compare with paper Figure 5 | Histogram |

### Deliverable
- Jupyter Notebook: `scripts/analysis/01_basic_statistics.ipynb`
- All charts with side-by-side comparisons to 2014 paper figures

---

## Phase 2 — Parallel Deep Analysis (Weeks 2-4)

> Each member owns one module. All three can work fully in parallel.

---

### Member A — Semantic Discovery

#### Purpose

The 2014 paper used **Jaccard similarity** (exact string matching) to determine schema similarity. For example, `"boro"` vs `"borough"` would be judged as non-matching, even though they are semantically identical. This led to 46% of NYC schemas being classified as "independent."

Semantic Discovery replaces exact string matching with **embedding-based semantic similarity**. After converting column names to vectors via an embedding model, semantically similar but differently spelled fields can be matched (e.g., `Embedding("boro")` vs `Embedding("borough")` -> cosine similarity ~ 0.92). The goal is to see if the 46% independence rate can be reduced.

#### Key Concepts

**Vector database choice:** The proposal mentions ChromaDB simply because it is the most lightweight option (`pip install chromadb`). With only 2,391 datasets, any tool works — FAISS, Qdrant, Pinecone, or even plain numpy cosine similarity matrices.

**Semantic Schema Clustering:** This directly contrasts with Member B's HAC + Jaccard approach (the paper's original method). B reproduces the baseline; A challenges it with modern techniques. Phase 3 compares the two.

#### Tasks

| # | Task | Description |
|---|---|---|
| A.1 | Vectorize metadata | Use OpenAI / HuggingFace Embeddings to vectorize dataset descriptions + column names |
| A.2 | Build vector index | Store in a vector database (ChromaDB / FAISS / numpy) for semantic search |
| A.3 | Semantic schema clustering | Replace Jaccard with embedding cosine similarity, redo schema clustering, compare with paper Figure 10's 46% independence rate |

**Output:** `scripts/analysis/02_semantic_discovery.ipynb`

---

### Member B — Data Quality & Schema Analysis

#### Purpose

Reproduce all data quality and schema structure analyses from the 2014 paper as a decade-comparison baseline. Also rebuild schema clustering using the paper's original method (Jaccard + HAC) so it can be compared with Member A's semantic approach in Phase 3.

#### Key Concepts

**Column type detection (paper Figure 12):** Count how many datasets contain specific column types:
- Geographic: latitude/longitude, address, zipcode
- Temporal: date, month, year

Method: regex + column name rules. E.g., column name containing `lat` / `longitude` or values matching coordinate patterns -> classified as lat/lon. Output is the proportion of datasets containing each type.

**Attribute Informativeness (paper Figure 14):** Measures whether column names are meaningful (human-readable). The paper's definition:
1. Tokenize column names by underscore
2. Filter out tokens with length <= 2
3. Check if each token exists in the **Wordlist Dictionary** (wordlist.sourceforge.net/pos-readme, paper ref. 25)
4. Informativeness = number of meaningful columns / total columns

Examples:
- `complaint_type` -> "complaint" (in dictionary) + "type" (in dictionary) -> informativeness = 1.0
- `q8a7a` -> not in dictionary -> informativeness = 0.0
- A dataset with 10 columns, 8 meaningful -> informativeness = 0.8

**HAC Schema Clustering (paper Figure 10):** This is the paper's **original method (baseline)** — must be reproduced to compare with Member A's semantic approach. Steps:
1. Each dataset's schema = set of all its column names
2. Compute pairwise Jaccard similarity = |A intersection B| / |A union B|
3. Apply HAC (Hierarchical Agglomerative Clustering) to iteratively merge the most similar clusters
4. At each similarity threshold (1.0, 0.9, 0.8, ..., 0.1), record the proportion of remaining independent clusters
5. Produce a curve chart in the same format as paper Figure 10

"46% independence rate" means: at threshold = 1 (requiring exact column name match to merge), 46% of schemas cannot find any exact match partner and remain as independent clusters.

#### Tasks

| # | Task | Description |
|---|---|---|
| B.1 | Null rate analysis | Use `cachedContents` `null` / `non_null` counts for each column, compare with paper Figure 13 |
| B.2 | Column type detection | Use regex + column names to detect lat/lon, date, address, zipcode type proportions, compare with paper Figure 12 |
| B.3 | Column naming quality | Compute attribute informativeness using Wordlist Dictionary, compare with paper Figure 14 |
| B.4 | HAC Schema Clustering (baseline) | Jaccard similarity + HAC to reproduce paper Figure 10's independence rate curve |
| B.5 | Tag Cloud | Generate tag clouds from metadata keywords, compare with paper Figure 4, 6 |
| B.6 | Geographic coverage analysis | Count zip code reference frequency, create geographic heatmap, compare with paper Figure 15 |

**Output:** `scripts/analysis/03_quality_schema.ipynb`

---

### Member C — Joinability Analysis

#### Purpose

Determine which datasets can be joined. Members A and B work from **column names**, while Member C adds a new dimension: examining **actual data values** within columns. Two columns with completely different names but highly overlapping value domains can be joined. The final joinability matrix in Phase 3 integrates signals from A (semantic), B (lexical), and C (instance-level).

#### Key Concepts

**Lazo algorithm:** A MinHash-based method for detecting column value overlap. Core idea:
1. For each column's values, use multiple hash functions to generate a fixed-size "signature" (MinHash signature)
2. Compare signatures between two columns to quickly estimate Jaccard containment (what proportion of A's values appear in B)
3. No need for value-by-value comparison — drastically reduced time complexity

Why it is needed:
```
Dataset A "borough" column: {MANHATTAN, BRONX, BROOKLYN, QUEENS, STATEN ISLAND}
Dataset B "boro" column:    {MANHATTAN, BRONX, BROOKLYN, QUEENS, STATEN ISLAND}
-> Different column names, but identical values -> Lazo catches this -> joinable
```

**LLM Schema Mapping:** Uses an LLM at the column level to judge whether two columns are semantically identical and joinable. Input: two column names + sample values. Output: "borough and boro refer to the same field." This complements Member A's embedding approach — A uses vector similarity automatically, C.2 uses LLM for more nuanced semantic reasoning.

**Joinability computation:** Integrates three signal layers, not just one method:

| Signal Layer | Method | Source |
|---|---|---|
| Column name lexical match | Jaccard similarity | Member B's results |
| Column name semantic similarity | Embedding cosine similarity | Member A's results |
| Column value overlap | Lazo (MinHash) | Member C's own computation |
| Comprehensive semantic judgment | LLM Schema Mapping | Member C's own computation |

**Lazo data source:** Uses the already-crawled 100 sample rows as each column's value domain representative. 100 rows is sufficient for low-cardinality columns (e.g., borough with only 5 values); precision decreases for high-cardinality columns (e.g., addresses), but works as an initial filter.

**Evaluation & Ground Truth:** Computing Precision / Recall / F1 requires ground truth. Ground truth is built in Phase 3 (after all methods have preliminary results). Steps:
1. Collect all column pairs that Lazo, Embedding, and Jaccard each identify as "possibly joinable"
2. Stratified sampling of 200 pairs:
   - High confidence (all 3 methods agree joinable): sample 50 pairs
   - Medium confidence (1-2 methods say joinable): sample 100 pairs — most valuable, where methods disagree
   - Low confidence (all say not joinable, random sample): sample 50 pairs
3. Each team member independently labels Yes / No
4. Majority vote -> ground truth
5. Evaluate each method's Precision, Recall, F1 against this ground truth

#### Tasks

| # | Task | Description |
|---|---|---|
| C.1 | Lazo implementation | Implement MinHash-based Lazo algorithm using sample rows to detect column value overlap |
| C.2 | LLM Schema Mapping | Design prompts for LLM to judge whether two columns (name + sample values) are semantically identical and joinable |

**Output:** `scripts/analysis/04_joinability.ipynb`

---

## Phase 3 — Synthesis & Report (Weeks 5-6)

> All three members converge results to produce final deliverables.

| # | Task | Lead | Description |
|---|---|---|---|
| 3.1 | Similarity Matrix | A + B + C | Integrate Jaccard (B) + Embedding (A) + Lazo/LLM (C) results into a joinability matrix, compare with paper Figure 11 |
| 3.2 | Ground Truth Labeling | All | Stratified sampling of 200 column pairs, all members label, establish evaluation benchmark |
| 3.3 | Performance Evaluation | A + C | Compute Precision, Recall, F1-score for each method against ground truth |
| 3.4 | Knowledge Graph | A + C | Build joinable relationship graph using NetworkX, identify Data Hub nodes |
| 3.5 | Decade Comparison Report | B | All 2014 vs 2026 metrics compiled into tables and charts |
| 3.6 | Final Report | All | Integrate all analyses, unify formatting, write conclusions |

### Final Deliverables
1. **NYC Data Landscape Report** — Comprehensive quantitative analysis of decade-long changes
2. **Connectivity Map** — Interactive Knowledge Graph visualization
3. **Technical Evaluation Review** — LLM vs traditional methods performance comparison

---

## Key 2014 Baseline Numbers (NYC)

> Quick reference to avoid re-reading the paper.

| Metric | 2014 Value | Source |
|---|---|---|
| Dataset count | 2,411 | Table 1 |
| Top categories | Social services, housing & development, city government | Table 1 |
| Tabular proportion (all cities) | 75% | Figure 2 |
| Schema independence at similarity=1 | 46% | Figure 10 |
| Schema variation across similarity levels | 26% (highest) | Figure 10 |
| Lat/Lon presence (all cities) | 52.9% | Figure 12 |
| Tables with date info | 40.4% | Figure 12 |
| Tables never modified (30 days) | 71% | Figure 8 |
| Table sparseness 0-0.1 (low null) | 63% | Figure 13 |



pd.DataFrame({
    "dataset_id_1": ...,
    "column_name_1": ...,
    "dataset_id_2": ...,
    "column_name_2": ...,
    "score": ...,          # 0~1 confidence(cosine similarity / Jaccard containment)
    "method": "jaccard"    # 或 "embedding" / "lazo"
})

A: combine 3 datasets and stratified sampling -> All: Ground Truth Labeling
B: PR curve for 3 methods
C: Knowledge Graph

