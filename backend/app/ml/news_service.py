"""
News fetching + vector-similarity feature extraction.

Ported from the Streamlit app's fetch_newsapi_articles / find_similar_events /
extract_news_features functions. All heavy dependencies (chromadb,
sentence-transformers, huggingface_hub) are imported lazily inside the
functions that need them, so the rest of the API works even before those
packages are installed or the ChromaDB collection is downloaded.
"""
import logging
import shutil
from pathlib import Path
from typing import Optional

import numpy as np
import requests

from app.config import get_settings

logger = logging.getLogger("app.ml.news_service")

TEXT_CHAR_CAP = 2000
STAGE2_FEATURE_ORDER = ["sentiment_score", "impact_score", "event_weight", "return_1d", "return_5d"]


def default_news_features() -> dict:
    return {
        "sentiment_score": 0.0,
        "impact_score": 0.0,
        "event_weight": 0.0,
        "news_count": 0,
        "has_supply_chain_event": 0,
    }


def fetch_news_articles(num_articles: int = 3) -> list:
    settings = get_settings()
    if not settings.NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not set — skipping news fetch, using neutral features.")
        return []

    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": "Apple AAPL",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": num_articles,
                "apiKey": settings.NEWS_API_KEY,
            },
            timeout=15,
        )
        data = resp.json()
        if data.get("status") != "ok":
            raise RuntimeError(data.get("message", "Unknown NewsAPI error"))

        articles = []
        for article in data.get("articles", []):
            title = article.get("title", "")
            body = article.get("description") or article.get("content", "")
            text = f"{title}. {body}".strip()[:TEXT_CHAR_CAP]
            articles.append(
                {
                    "title": title,
                    "source": (article.get("source") or {}).get("name", "Unknown"),
                    "published_at": article.get("publishedAt", "n/a"),
                    "url": article.get("url", ""),
                    "text": text,
                }
            )
        return articles
    except Exception as exc:
        logger.error("NewsAPI request failed: %s", exc)
        return []


def get_or_download_chroma_path() -> Optional[Path]:
    settings = get_settings()
    cache_dir = Path(settings.CHROMA_CACHE_DIR)
    local_path = cache_dir / settings.HF_COLLECTION_NAME
    if local_path.exists():
        return local_path

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        logger.warning("huggingface_hub not installed — skipping ChromaDB download.")
        return None

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        repo_path = snapshot_download(repo_id=settings.HF_REPO_ID)
        source = Path(repo_path) / settings.HF_COLLECTION_NAME
        if not source.exists():
            logger.warning("Collection '%s' not found in HF repo %s", settings.HF_COLLECTION_NAME, settings.HF_REPO_ID)
            return None
        if local_path.exists():
            shutil.rmtree(local_path)
        shutil.copytree(source, local_path)
        return local_path
    except Exception as exc:
        logger.error("Failed to download ChromaDB collection from HuggingFace: %s", exc)
        return None


_collection_cache = {}
_encoder_cache = {}


def load_collection():
    if "collection" in _collection_cache:
        return _collection_cache["collection"]

    try:
        import chromadb
    except ImportError:
        logger.warning("chromadb not installed — similarity search disabled.")
        _collection_cache["collection"] = None
        return None

    chroma_path = get_or_download_chroma_path()
    if chroma_path is None:
        _collection_cache["collection"] = None
        return None

    try:
        client = chromadb.PersistentClient(path=str(chroma_path))
        names = [c.name for c in client.list_collections()]
        if "aapl_events" not in names:
            logger.warning("Collection 'aapl_events' not found at %s. Present: %s", chroma_path, names)
            _collection_cache["collection"] = None
            return None
        collection = client.get_collection(name="aapl_events")
        _collection_cache["collection"] = collection
        return collection
    except Exception as exc:
        logger.error("Failed to load ChromaDB collection: %s", exc)
        _collection_cache["collection"] = None
        return None


def load_encoder():
    if "encoder" in _encoder_cache:
        return _encoder_cache["encoder"]
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.warning("sentence-transformers not installed — similarity search disabled.")
        _encoder_cache["encoder"] = None
        return None
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    _encoder_cache["encoder"] = encoder
    return encoder


def find_similar_events(query_text: str, top_k: int = 5):
    collection = load_collection()
    encoder = load_encoder()
    if collection is None or encoder is None:
        return None, 0
    try:
        count = collection.count()
        if count == 0:
            return None, 0
        query_embedding = encoder.encode(query_text[:TEXT_CHAR_CAP]).tolist()
        results = collection.query(query_embeddings=[query_embedding], n_results=min(top_k, count))
        return results, count
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        return None, 0


def extract_news_features(results) -> dict:
    if results is None or not results.get("metadatas") or not results["metadatas"][0]:
        return default_news_features()

    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    similarities = 1 - np.array(distances)
    total_sim = similarities.sum()
    if total_sim == 0:
        return default_news_features()
    weights = similarities / total_sim

    return {
        "sentiment_score": float(np.average([float(m.get("sentiment_score", 0)) for m in metadatas], weights=weights)),
        "impact_score": float(np.average([float(m.get("impact_score", 0)) for m in metadatas], weights=weights)),
        "event_weight": float(np.average([float(m.get("event_weight", 0)) for m in metadatas], weights=weights)),
        "news_count": len(metadatas),
        "has_supply_chain_event": int(any(m.get("event_type") == "supply_chain" for m in metadatas)),
    }


def get_aggregated_news_features(top_k: int = 5) -> tuple[dict, list]:
    """Fetch articles, run similarity search for each, and average the results.

    Returns (aggregated_features, similar_events_for_display).
    """
    articles = fetch_news_articles(num_articles=3)
    if not articles:
        return default_news_features(), []

    all_features = []
    similar_events = []
    for article in articles:
        results, count = find_similar_events(article["text"], top_k=top_k)
        feats = extract_news_features(results)
        all_features.append(feats)
        if results and results.get("metadatas") and results["metadatas"][0]:
            for meta, dist in zip(results["metadatas"][0][:1], results["distances"][0][:1]):
                similar_events.append(
                    {
                        "title": meta.get("title", article["title"]),
                        "date": meta.get("date", "n/a"),
                        "similarity": round(1 - dist, 4),
                        "direction": meta.get("direction", "NEUTRAL"),
                    }
                )

    keys = all_features[0].keys()
    aggregated = {k: float(np.mean([f[k] for f in all_features])) for k in keys}
    aggregated["news_count"] = int(sum(f["news_count"] for f in all_features))
    aggregated["has_supply_chain_event"] = int(any(f["has_supply_chain_event"] for f in all_features))
    return aggregated, similar_events
