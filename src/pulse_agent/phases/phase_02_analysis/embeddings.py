from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

_EMBEDDING_METHOD: str | None = None


def embedding_method() -> str:
    global _EMBEDDING_METHOD
    if _EMBEDDING_METHOD is not None:
        return _EMBEDDING_METHOD
    try:
        import sentence_transformers  # noqa: F401

        _EMBEDDING_METHOD = "sentence_transformers"
    except ImportError:
        _EMBEDDING_METHOD = "tfidf"
    return _EMBEDDING_METHOD


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)

    method = embedding_method()
    if method == "sentence_transformers":
        try:
            return _embed_sentence_transformers(texts)
        except Exception as exc:
            logger.warning("sentence-transformers failed, falling back to tfidf: %s", exc)

    return _embed_tfidf(texts)


def _embed_sentence_transformers(texts: list[str]) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    model_name = "all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)


def _embed_tfidf(texts: list[str]) -> np.ndarray:
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(max_features=384, stop_words="english")
    matrix = vectorizer.fit_transform(texts)
    return np.asarray(matrix.toarray(), dtype=np.float32)
