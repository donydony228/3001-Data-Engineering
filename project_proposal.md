# Project Plan: The Evolution of NYC Open Data—Tracking a Decade of Change in Scale, Quality, and Integration Potential

## Project Objective
This project aims to conduct a **modernized research study** on the New York City open data portal, replicating and upgrading the classic 2014 landscape survey by Barbosa et al.. We will leverage **Large Language Models (LLMs)**, **Vector Embeddings**, and the **Lazo algorithm** to quantify the evolution of data scale, quality, and integration potential over the past decade.

---

## I. Execution Steps and Task Descriptions

### 1. Infrastructure and Data Acquisition
**Baseline Reference:** The **2,411 datasets** from NYC analyzed in the 2014 study.

*   **Data to be Used:**
    *   Current **Metadata** (titles, descriptions, categories, download counts) fetched via the **Socrata SODA API**.
    *   **Sample rows** (the first 100 non-null values) from each dataset to be used for type detection and profiling.
*   **Questions to Answer:**
    *   **Growth Scale:** Compared to the 2,411 datasets in 2014, what is the current growth rate of NYC's data volume (now ~3,009)?
    *   **Format Evolution:** In 2014, approximately **75%** of all datasets across cities were tabular; has the proportion of machine-readable structured data in NYC changed since then?
*   **Specific Tasks:**
    *   Develop an automated Python-based crawler.
    *   Establish a centralized database (e.g., DuckDB or PostgreSQL) to manage all ingested metadata.
    *   Generate a statistical distribution of current data formats to compare against 2014 benchmarks.

### 2. Semantic Discovery and Quality Profiling
**Baseline Reference:** The 2014 finding that **46%** of NYC's initial schema clusters remained independent at a similarity of 1, with the **highest variation (26%)** across similarity levels among all cities studied.

*   **Data to be Used:** Vectorized dataset descriptions, column headers, and sample instances.
*   **Questions to Answer:**
    *   **Heterogeneity Challenge:** Can modern **semantic search** further reduce the 46% of schemata that were previously judged independent due to naming discrepancies (e.g., "BName" vs. "Borough")?
    *   **Health Evolution:** Are current null rates and data sparsity levels improved compared to a decade ago?
*   **Specific Tasks:**
    *   Vectorize metadata using **OpenAI/HuggingFace Embeddings** and index them in a **ChromaDB** vector database.
    *   Utilize **LLM Agents** to automatically tag and re-categorize the "independent" clusters from the 2014 study to find hidden semantic overlaps.
    *   Integrate the **Great Expectations** framework to automatically profile data health metrics like null rates and schema drift.

### 3. Hybrid Joinability Benchmarking
**Baseline Reference:** The 2014 observation that spatiotemporal types (latitude/longitude) were present in over **52.9%** of all city datasets, with NYC having extensive 311 service request data creating large schema overlaps.

*   **Data to be Used:** Sets of values for numerical/categorical columns and spatio-temporal coordinates.
*   **Questions to Answer:**
    *   **Technical Performance:** In identifying "non-trivial joins," do **LLM Agents** outperform the MinHash-based **Lazo algorithm** in terms of precision and recall?
    *   **Geospatial Connectivity:** Does NYC's high proportion of spatial data effectively "stitch" datasets together despite linguistic heterogeneity?
*   **Specific Tasks:**
    *   Implement **Lazo** to detect cardinality-based overlaps in numerical and categorical values.
    *   Design **LLM Prompts** (e.g., following Table GPT or Magneto logic) to perform "Schema Mapping" between columns with different names but identical semantics.
    *   Calculate **Precision, Recall, and F1-score** to quantify the effectiveness of these modern techniques.

### 4. NYC Data Knowledge Graph and Synthesis
*   **Data to be Used:** All "joinable" relationships confirmed in the previous phases.
*   **Questions to Answer:**
    *   **Hub Identification:** Which datasets act as "Data Hubs" in the current NYC ecosystem (e.g., 311 requests, Zip Code, or Timestamp tables)?
    *   **Decade Overview:** Has the overall landscape shifted in connectivity and integration potential from 2014 to today?
*   **Specific Tasks:**
    *   Model the ecosystem as a **Knowledge Graph** using **NetworkX or Neo4j** to visualize connectivity.
    *   Produce a comparative synthesis report featuring charts and statistics that contrast 2014 baseline results with 2026 findings.

---

## II. Expected Deliverables
1.  **NYC Data Landscape Report:** A comprehensive document detailing growth, format shifts, and quality distributions with quantitative comparisons to 2014 data.
2.  **Connectivity Map:** An interactive network visualization showing how NYC's datasets relate through semantic embeddings and spatial coordinates.
3.  **Technical Evaluation Review:** A report quantifying the performance of LLMs vs. traditional Jaccard/Lazo methods in handling NYC's heterogeneous fields.

---

## III. Why NYC?
We have chosen NYC because it was the **most data-rich city** in the 2014 study with 2,411 datasets—now grown to ~3,009. NYC provides the richest baseline data in the original paper, including detailed **schema similarity matrices** (Figure 11), **tag cloud analysis** (Figure 4), **geographic coverage heatmaps** (Figure 15), and **schema diversity curves** (Figure 10 — 46% independence with 26% variation, the highest among all cities). NYC also remains on the **Socrata platform**, ensuring full API consistency between the 2014 baseline and our 2026 replication. This combination of abundant baseline metrics and platform continuity makes NYC the ideal candidate for a rigorous decade-long longitudinal comparison.
