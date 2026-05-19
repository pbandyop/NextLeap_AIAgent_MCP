from datetime import date

import numpy as np

from pulse_agent.models.review import Review, ReviewSource
from pulse_agent.phases.phase_02_analysis.clustering import cluster_reviews, review_texts
from pulse_agent.phases.phase_02_analysis.embeddings import embed_texts


def _review(rid: str, rating: int, body: str) -> Review:
    return Review(
        source=ReviewSource.PLAY_STORE,
        review_id=rid,
        rating=rating,
        title="Title",
        body=body,
        review_date=date(2026, 5, 1),
    )


def test_embed_and_cluster_synthetic():
    reviews = [
        _review(f"r{i}", 5 if i % 2 == 0 else 1, f"Review text number {i} about investing and app quality.")
        for i in range(12)
    ]
    embeddings = embed_texts(review_texts(reviews))
    assert embeddings.shape[0] == len(reviews)
    clusters, method = cluster_reviews(
        reviews, embeddings, max_clusters=3, min_cluster_size=2
    )
    assert method
    assert clusters
    assert sum(len(v) for v in clusters.values()) >= 1


def test_cluster_empty():
    clusters, method = cluster_reviews([], np.zeros((0, 8)), max_clusters=3)
    assert clusters == {}
    assert method == "none"
