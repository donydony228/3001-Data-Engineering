"""
Build the final dataset connectivity graph and focused hub visualization.

Inputs:
  - merged_column_pairs.parquet
      Column-pair candidates with Jaccard, Lazo, embedding votes, and vote_count.
  - data/nyc_socrata_datasets.json
      NYC Socrata dataset metadata used for readable names and categories.

Pipeline:
  1. Keep high-confidence column matches where vote_count >= 2.
  2. Collapse column matches into weighted dataset-to-dataset edges.
     Edge weight = number of matched column pairs between two datasets.
  3. Build the full dataset graph for metrics.
  4. Rank dataset hubs by weighted degree.
  5. Build a focused presentation graph from the top hubs, their strongest
     neighbors, and the strongest edges among those selected datasets.

Outputs:
  - dataset_connectivity_edges.csv
  - dataset_connectivity_nodes.csv
  - category_node_summary.csv
  - category_edge_summary.csv
  - dataset_connectivity_focused_graph.png
  - dataset_connectivity_focused_graph.html
  - dataset_connectivity_summary.md
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

OUTPUT_CACHE = Path("outputs")
(OUTPUT_CACHE / ".matplotlib").mkdir(parents=True, exist_ok=True)
(OUTPUT_CACHE / ".cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str((OUTPUT_CACHE / ".matplotlib").resolve()))
os.environ.setdefault("XDG_CACHE_HOME", str((OUTPUT_CACHE / ".cache").resolve()))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


DEFAULT_PAIRS = Path("merged_column_pairs.parquet")
DEFAULT_METADATA = Path("data/nyc_socrata_datasets.json")
DEFAULT_OUTPUT_DIR = Path("outputs/dataset_connectivity")

DEFAULT_MIN_VOTES = 2
DEFAULT_FOCUSED_HUBS = 4
DEFAULT_NEIGHBORS_PER_HUB = 14
DEFAULT_MAX_EDGES = 90


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a focused dataset connectivity graph from merged column-pair matches."
    )
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-votes", type=int, default=DEFAULT_MIN_VOTES)
    parser.add_argument("--focused-hubs", type=int, default=DEFAULT_FOCUSED_HUBS)
    parser.add_argument(
        "--focused-neighbors-per-hub",
        type=int,
        default=DEFAULT_NEIGHBORS_PER_HUB,
    )
    parser.add_argument("--focused-max-edges", type=int, default=DEFAULT_MAX_EDGES)
    return parser.parse_args()


def load_metadata(metadata_path: Path) -> dict[str, dict[str, str]]:
    with metadata_path.open("r", encoding="utf-8") as f:
        datasets = json.load(f)

    metadata = {}
    for dataset in datasets:
        dataset_id = str(dataset.get("id", ""))
        if not dataset_id:
            continue

        full_metadata = dataset.get("full_metadata") or {}
        metadata[dataset_id] = {
            "name": dataset.get("name") or dataset_id,
            "category": full_metadata.get("category") or "Unknown",
        }

    return metadata


def load_high_confidence_column_pairs(pairs_path: Path, min_votes: int) -> pd.DataFrame:
    columns = [
        "dataset_id_1",
        "column_name_1",
        "dataset_id_2",
        "column_name_2",
        "jaccard_score",
        "lazo_score",
        "embedding_score",
        "j_vote",
        "l_vote",
        "e_vote",
        "vote_count",
    ]

    pairs = pd.read_parquet(pairs_path, columns=columns, engine="fastparquet")
    pairs = pairs[pairs["vote_count"] >= min_votes].copy()

    dataset_1 = pairs["dataset_id_1"].astype(str)
    dataset_2 = pairs["dataset_id_2"].astype(str)
    pairs["source"] = dataset_1.where(dataset_1 < dataset_2, dataset_2)
    pairs["target"] = dataset_2.where(dataset_1 < dataset_2, dataset_1)

    return pairs[pairs["source"] != pairs["target"]].copy()


def collapse_to_dataset_edges(column_pairs: pd.DataFrame) -> pd.DataFrame:
    edges = column_pairs.groupby(["source", "target"], as_index=False).agg(
        matched_column_count=("vote_count", "size"),
        avg_vote_count=("vote_count", "mean"),
        max_vote_count=("vote_count", "max"),
        avg_jaccard_score=("jaccard_score", "mean"),
        max_jaccard_score=("jaccard_score", "max"),
        avg_lazo_score=("lazo_score", "mean"),
        max_lazo_score=("lazo_score", "max"),
        avg_embedding_score=("embedding_score", "mean"),
        max_embedding_score=("embedding_score", "max"),
        jaccard_match_count=("j_vote", "sum"),
        lazo_match_count=("l_vote", "sum"),
        embedding_match_count=("e_vote", "sum"),
    )

    return edges.sort_values(
        ["matched_column_count", "avg_vote_count"],
        ascending=[False, False],
    ).reset_index(drop=True)


def add_edge_metadata(
    edges: pd.DataFrame,
    metadata: dict[str, dict[str, str]],
) -> pd.DataFrame:
    edges = edges.copy()
    edges["source_name"] = edges["source"].map(
        lambda dataset_id: metadata.get(dataset_id, {}).get("name", dataset_id)
    )
    edges["target_name"] = edges["target"].map(
        lambda dataset_id: metadata.get(dataset_id, {}).get("name", dataset_id)
    )
    edges["source_category"] = edges["source"].map(
        lambda dataset_id: metadata.get(dataset_id, {}).get("category", "Unknown")
    )
    edges["target_category"] = edges["target"].map(
        lambda dataset_id: metadata.get(dataset_id, {}).get("category", "Unknown")
    )
    return edges


def build_full_graph(edges: pd.DataFrame) -> nx.Graph:
    graph = nx.Graph()

    for row in edges.itertuples(index=False):
        graph.add_edge(
            row.source,
            row.target,
            weight=int(row.matched_column_count),
            avg_vote_count=float(row.avg_vote_count),
            max_vote_count=int(row.max_vote_count),
            avg_jaccard_score=float(row.avg_jaccard_score),
            avg_lazo_score=float(row.avg_lazo_score),
            avg_embedding_score=float(row.avg_embedding_score),
        )

    return graph


def compute_node_metrics(
    graph: nx.Graph,
    metadata: dict[str, dict[str, str]],
) -> pd.DataFrame:
    degree = dict(graph.degree())
    weighted_degree = dict(graph.degree(weight="weight"))
    degree_centrality = nx.degree_centrality(graph)
    pagerank = nx.pagerank(graph, weight="weight")

    rows = []
    for node in graph.nodes:
        info = metadata.get(node, {})
        rows.append(
            {
                "dataset_id": node,
                "name": info.get("name", node),
                "category": info.get("category", "Unknown"),
                "degree": degree.get(node, 0),
                "weighted_degree": weighted_degree.get(node, 0.0),
                "degree_centrality": degree_centrality.get(node, 0.0),
                "pagerank": pagerank.get(node, 0.0),
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["weighted_degree", "degree"],
        ascending=[False, False],
    )


def build_category_summaries(
    node_metrics: pd.DataFrame,
    edges: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    category_nodes = (
        node_metrics.groupby("category", as_index=False)
        .agg(
            dataset_count=("dataset_id", "size"),
            avg_degree=("degree", "mean"),
            avg_weighted_degree=("weighted_degree", "mean"),
            max_weighted_degree=("weighted_degree", "max"),
        )
        .sort_values(["dataset_count", "avg_weighted_degree"], ascending=False)
    )

    category_pair = edges.apply(
        lambda row: " / ".join(sorted([row["source_category"], row["target_category"]])),
        axis=1,
    )
    category_edges = (
        edges.assign(category_pair=category_pair)
        .groupby("category_pair", as_index=False)
        .agg(
            dataset_edge_count=("matched_column_count", "size"),
            total_matched_columns=("matched_column_count", "sum"),
            avg_matched_columns=("matched_column_count", "mean"),
        )
        .sort_values(["total_matched_columns", "dataset_edge_count"], ascending=False)
    )

    return category_nodes, category_edges


def build_focused_hub_graph(
    full_graph: nx.Graph,
    node_metrics: pd.DataFrame,
    hub_count: int,
    neighbors_per_hub: int,
    max_edges: int,
) -> tuple[nx.Graph, set[str]]:
    hub_ids = select_hubs(node_metrics, full_graph, hub_count)
    selected_nodes, required_edges = select_hub_neighborhoods(
        full_graph,
        hub_ids,
        neighbors_per_hub,
    )

    induced = full_graph.subgraph(selected_nodes).copy()
    ranked_edges = sorted(
        induced.edges(data=True),
        key=lambda edge: edge[2].get("weight", 1),
        reverse=True,
    )

    focused = nx.Graph()
    focused.add_nodes_from(selected_nodes)

    for source, target in required_edges:
        if induced.has_edge(source, target):
            focused.add_edge(source, target, **induced[source][target])

    for source, target, attrs in ranked_edges:
        if focused.number_of_edges() >= max_edges:
            break
        focused.add_edge(source, target, **attrs)

    focused.remove_nodes_from(list(nx.isolates(focused)))
    return focused, set(hub_ids)


def select_hubs(
    node_metrics: pd.DataFrame,
    graph: nx.Graph,
    hub_count: int,
) -> list[str]:
    hub_ids = []
    categories_seen = set()

    for row in node_metrics.itertuples(index=False):
        if row.category in categories_seen and len(hub_ids) < hub_count - 1:
            continue
        if row.dataset_id not in graph:
            continue

        hub_ids.append(row.dataset_id)
        categories_seen.add(row.category)

        if len(hub_ids) >= hub_count:
            break

    return hub_ids


def select_hub_neighborhoods(
    graph: nx.Graph,
    hub_ids: list[str],
    neighbors_per_hub: int,
) -> tuple[set[str], set[tuple[str, str]]]:
    selected_nodes = set(hub_ids)
    selected_edges = set()

    for hub in hub_ids:
        strongest_neighbors = sorted(
            graph[hub].items(),
            key=lambda item: item[1].get("weight", 1),
            reverse=True,
        )[:neighbors_per_hub]

        for neighbor, _attrs in strongest_neighbors:
            selected_nodes.add(neighbor)
            selected_edges.add(tuple(sorted((hub, neighbor))))

    return selected_nodes, selected_edges


def draw_focused_png(
    graph: nx.Graph,
    hubs: set[str],
    node_metrics: pd.DataFrame,
    metadata: dict[str, dict[str, str]],
    output_path: Path,
) -> None:
    plt.figure(figsize=(16, 11))

    local_weighted_degree = dict(graph.degree(weight="weight"))
    edge_widths = [
        0.6 + 0.55 * math.log1p(graph.edges[edge].get("weight", 1))
        for edge in graph.edges
    ]
    node_sizes = [
        1450 if node in hubs else 360 + 30 * math.sqrt(max(local_weighted_degree.get(node, 1), 1))
        for node in graph.nodes
    ]

    hub_palette = ["#2f80ed", "#f2994a", "#27ae60", "#9b51e0", "#eb5757"]
    hub_color = {hub: hub_palette[i % len(hub_palette)] for i, hub in enumerate(sorted(hubs))}
    node_colors = [hub_color.get(node, "#d9d9d9") for node in graph.nodes]

    pos = nx.spring_layout(graph, weight="weight", seed=11, iterations=250, k=0.75)

    nx.draw_networkx_edges(
        graph,
        pos,
        width=edge_widths,
        alpha=0.36,
        edge_color="#9a9a9a",
    )
    nx.draw_networkx_nodes(
        graph,
        pos,
        node_size=node_sizes,
        node_color=node_colors,
        linewidths=0.9,
        edgecolors="#555555",
        alpha=0.96,
    )

    label_nodes = set(hubs) | set(
        node_metrics[node_metrics["dataset_id"].isin(set(graph.nodes) - hubs)]
        .sort_values(["weighted_degree", "degree"], ascending=False)
        .head(18)["dataset_id"]
    )
    labels = {
        node: shorten_label(
            metadata.get(node, {}).get("name", node),
            max_len=30 if node in hubs else 24,
        )
        for node in label_nodes
        if node in graph
    }
    nx.draw_networkx_labels(
        graph,
        pos,
        labels=labels,
        font_size=8,
        font_color="#222222",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 1.2},
    )

    plt.title(
        "Focused Dataset Connectivity Graph\n"
        "Colored nodes are high weighted-degree hubs; gray nodes are their strongest connected datasets",
        fontsize=15,
        fontweight="bold",
    )
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=220)
    plt.close()


def draw_focused_html(
    graph: nx.Graph,
    hubs: set[str],
    node_metrics: pd.DataFrame,
    metadata: dict[str, dict[str, str]],
    output_path: Path,
) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("plotly is not installed; skipping HTML output.")
        return

    pos = nx.spring_layout(graph, weight="weight", seed=11, iterations=250, k=0.75)
    metrics = node_metrics.set_index("dataset_id").to_dict("index")

    edge_traces = []
    for source, target, attrs in graph.edges(data=True):
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        weight = float(attrs.get("weight", 1))
        edge_traces.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line={
                    "width": 0.7 + 0.8 * math.log1p(weight),
                    "color": "rgba(130,130,130,0.45)",
                },
                hoverinfo="text",
                text=f"{source} - {target}: {weight:.0f} matched columns",
                showlegend=False,
            )
        )

    local_weighted_degree = dict(graph.degree(weight="weight"))
    hub_palette = ["#2f80ed", "#f2994a", "#27ae60", "#9b51e0", "#eb5757"]
    hub_color = {hub: hub_palette[i % len(hub_palette)] for i, hub in enumerate(sorted(hubs))}

    node_x = []
    node_y = []
    node_size = []
    node_color = []
    hover_text = []

    for node in graph.nodes:
        x, y = pos[node]
        info = metadata.get(node, {})
        row = metrics.get(node, {})
        node_x.append(x)
        node_y.append(y)
        node_size.append(28 if node in hubs else min(24, 10 + 2.2 * math.sqrt(max(local_weighted_degree.get(node, 1), 1))))
        node_color.append(hub_color.get(node, "#cfcfcf"))
        hover_text.append(
            "<br>".join(
                [
                    f"<b>{info.get('name', node)}</b>",
                    f"ID: {node}",
                    f"Category: {info.get('category', 'Unknown')}",
                    f"Hub: {'yes' if node in hubs else 'no'}",
                    f"Degree: {row.get('degree', 0)}",
                    f"Weighted degree: {row.get('weighted_degree', 0):.0f}",
                ]
            )
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        hovertext=hover_text,
        marker={
            "color": node_color,
            "size": node_size,
            "line": {"width": 0.8, "color": "#444444"},
        },
    )

    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            title="Focused NYC Open Data Connectivity Graph",
            showlegend=False,
            hovermode="closest",
            margin={"b": 20, "l": 5, "r": 5, "t": 45},
            xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        ),
    )
    fig.write_html(output_path)


def write_summary(
    output_path: Path,
    pairs_path: Path,
    min_votes: int,
    filtered_pair_count: int,
    full_graph: nx.Graph,
    focused_graph: nx.Graph,
    node_metrics: pd.DataFrame,
    edges: pd.DataFrame,
) -> None:
    top_nodes = node_metrics.head(10)[
        ["dataset_id", "name", "category", "degree", "weighted_degree", "pagerank"]
    ]
    top_edges = edges.head(10)[
        ["source", "target", "source_name", "target_name", "matched_column_count", "avg_vote_count"]
    ]

    text = [
        "# Dataset Connectivity Graph Summary",
        "",
        f"Input pairs: `{pairs_path}`",
        f"Column-pair threshold: `vote_count >= {min_votes}`",
        f"Filtered column-pair matches: `{filtered_pair_count:,}`",
        "",
        "## Full Graph",
        "",
        f"Nodes: `{full_graph.number_of_nodes():,}`",
        f"Edges: `{full_graph.number_of_edges():,}`",
        f"Connected components: `{nx.number_connected_components(full_graph):,}`",
        "",
        "## Focused Visualization",
        "",
        f"Nodes: `{focused_graph.number_of_nodes():,}`",
        f"Edges: `{focused_graph.number_of_edges():,}`",
        "",
        "## Top Datasets By Weighted Degree",
        "",
        "```",
        top_nodes.to_string(index=False),
        "```",
        "",
        "## Strongest Dataset Edges",
        "",
        "```",
        top_edges.to_string(index=False),
        "```",
        "",
    ]
    output_path.write_text("\n".join(text), encoding="utf-8")


def shorten_label(label: str, max_len: int = 34) -> str:
    label = " ".join(str(label).split())
    if len(label) <= max_len:
        return label
    return label[: max_len - 3] + "..."


def write_outputs(
    output_dir: Path,
    edges: pd.DataFrame,
    node_metrics: pd.DataFrame,
    category_nodes: pd.DataFrame,
    category_edges: pd.DataFrame,
    focused_graph: nx.Graph,
    focused_hubs: set[str],
    metadata: dict[str, dict[str, str]],
    pairs_path: Path,
    min_votes: int,
    filtered_pair_count: int,
    full_graph: nx.Graph,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    edges.to_csv(output_dir / "dataset_connectivity_edges.csv", index=False)
    node_metrics.to_csv(output_dir / "dataset_connectivity_nodes.csv", index=False)
    category_nodes.to_csv(output_dir / "category_node_summary.csv", index=False)
    category_edges.to_csv(output_dir / "category_edge_summary.csv", index=False)

    draw_focused_png(
        focused_graph,
        focused_hubs,
        node_metrics,
        metadata,
        output_dir / "dataset_connectivity_focused_graph.png",
    )
    draw_focused_html(
        focused_graph,
        focused_hubs,
        node_metrics,
        metadata,
        output_dir / "dataset_connectivity_focused_graph.html",
    )
    write_summary(
        output_dir / "dataset_connectivity_summary.md",
        pairs_path,
        min_votes,
        filtered_pair_count,
        full_graph,
        focused_graph,
        node_metrics,
        edges,
    )


def main() -> None:
    args = parse_args()

    print(f"Loading metadata from {args.metadata}")
    metadata = load_metadata(args.metadata)

    print(f"Loading merged column pairs from {args.pairs}")
    column_pairs = load_high_confidence_column_pairs(args.pairs, args.min_votes)
    print(f"Kept {len(column_pairs):,} column-pair matches with vote_count >= {args.min_votes}")

    print("Collapsing column pairs into dataset edges")
    dataset_edges = collapse_to_dataset_edges(column_pairs)
    dataset_edges = add_edge_metadata(dataset_edges, metadata)

    print("Building full graph")
    full_graph = build_full_graph(dataset_edges)
    print(
        f"Full graph: {full_graph.number_of_nodes():,} nodes, "
        f"{full_graph.number_of_edges():,} edges"
    )

    print("Computing node metrics")
    node_metrics = compute_node_metrics(full_graph, metadata)
    category_nodes, category_edges = build_category_summaries(node_metrics, dataset_edges)

    print("Building focused hub graph")
    focused_graph, focused_hubs = build_focused_hub_graph(
        full_graph,
        node_metrics,
        args.focused_hubs,
        args.focused_neighbors_per_hub,
        args.focused_max_edges,
    )
    print(
        f"Focused graph: {focused_graph.number_of_nodes():,} nodes, "
        f"{focused_graph.number_of_edges():,} edges, "
        f"{len(focused_hubs):,} hubs"
    )

    print(f"Writing outputs to {args.output_dir}")
    write_outputs(
        args.output_dir,
        dataset_edges,
        node_metrics,
        category_nodes,
        category_edges,
        focused_graph,
        focused_hubs,
        metadata,
        args.pairs,
        args.min_votes,
        len(column_pairs),
        full_graph,
    )

    print("Done.")


if __name__ == "__main__":
    main()
