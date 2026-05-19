from __future__ import annotations

import logging
from collections import defaultdict

import numpy as np

from pulse_agent.models.review import Review
from pulse_agent.phases.phase_01_ingestion.content_filters import combined_review_text

logger = logging.getLogger(__name__)


def cluster_reviews(
    reviews: list[Review],
    embeddings: np.ndarray,
    *,
    max_clusters: int,
    min_cluster_size: int = 10,
) -> tuple[dict[int, list[Review]], str]:
    """
    Group reviews by cluster label. Returns clusters keyed by label (noise excluded)
    and the clustering method name.
    """
    if len(reviews) == 0:
        return {}, "none"
    if len(reviews) <= min_cluster_size:
        return {0: list(reviews)}, "single"

    labels, method = _compute_labels(embeddings, len(reviews), min_cluster_size, max_clusters)
    grouped: dict[int, list[Review]] = defaultdict(list)
    for review, label in zip(reviews, labels, strict=True):
        if label < 0:
            continue
        grouped[int(label)].append(review)

    if not grouped:
        return {0: list(reviews)}, f"{method}_fallback_single"

    ranked = sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)
    top = dict(ranked[:max_clusters])
    return top, method


def _compute_labels(
    embeddings: np.ndarray,
    n_samples: int,
    min_cluster_size: int,
    max_clusters: int,
) -> tuple[np.ndarray, str]:
    if n_samples < 4:
        return np.zeros(n_samples, dtype=int), "trivial"

    try:
        return _hdbscan_labels(embeddings, min_cluster_size), "umap_hdbscan"
    except Exception as exc:
        logger.debug("HDBSCAN path unavailable: %s", exc)

    return _kmeans_labels(embeddings, max_clusters), "kmeans"


def _hdbscan_labels(embeddings: np.ndarray, min_cluster_size: int) -> np.ndarray:
    import hdbscan
    import umap

    n_neighbors = min(15, max(2, len(embeddings) - 1))
    reduced = umap.UMAP(
        n_neighbors=n_neighbors,
        n_components=min(10, len(embeddings) - 1),
        metric="cosine",
        random_state=42,
    ).fit_transform(embeddings)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=max(2, min_cluster_size // 2),
        metric="euclidean",
    )
    return clusterer.fit_predict(reduced)


def _kmeans_labels(embeddings: np.ndarray, max_clusters: int) -> np.ndarray:
    from sklearn.cluster import KMeans

    k = min(max_clusters, max(1, len(embeddings) // 5))
    k = max(1, k)
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    return model.fit_predict(embeddings)


def review_texts(reviews: list[Review]) -> list[str]:
    return [combined_review_text(r) for r in reviews]
