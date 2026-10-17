"""Unsupervised text models: NMF topics, TF-IDF keywords, KMeans clusters. No labels are used here."""
import warnings

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import NMF, PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from sklearn.preprocessing import Normalizer

from .nlp import analyzer_unigram_bigram, tokenize


def _top_terms(row: np.ndarray, names: np.ndarray, n: int) -> list[str]:
    return [str(names[i]) for i in np.argsort(-row)[:n] if row[i] > 0]


def dedupe_phrases(terms: list[str], limit: int) -> list[str]:
    """Drop unigrams already covered by a chosen bigram (and vice versa order-preserving)."""
    out: list[str] = []
    for t in terms:
        if any((t in o.split()) or (o in t.split()) for o in out if o != t):
            continue
        out.append(t)
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------- topics
def fit_topics(texts: list[str], k: int = 8, seed: int = 0) -> dict | None:
    if len(texts) < 50:
        return None
    vec = TfidfVectorizer(analyzer=tokenize, min_df=5, max_df=0.25, sublinear_tf=True)
    X = vec.fit_transform(texts)
    if X.shape[1] < k * 2:
        return None
    nmf = NMF(n_components=k, init="nndsvda", random_state=seed, max_iter=500)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        W = nmf.fit_transform(X)
    names = vec.get_feature_names_out()
    topics = []
    for t in range(k):
        reps = np.argsort(-W[:, t])[:3]
        topics.append({"topic_id": t, "terms": _top_terms(nmf.components_[t], names, 10),
                       "label": " / ".join(_top_terms(nmf.components_[t], names, 3)),
                       "representative_idx": [int(i) for i in reps]})
    return {"vec": vec, "nmf": nmf, "topics": topics, "assignment": W.argmax(1),
            "reconstruction_err": float(nmf.reconstruction_err_)}


def assign_topics(model: dict, texts: list[str]) -> np.ndarray:
    return model["nmf"].transform(model["vec"].transform(texts)).argmax(1)


# ---------------------------------------------------------------- keywords / clusters
def make_keyword_vec() -> TfidfVectorizer:
    return TfidfVectorizer(analyzer=analyzer_unigram_bigram, min_df=3, max_df=0.25, sublinear_tf=True)


def doc_keywords(X, names: np.ndarray, n: int = 5) -> list[list[str]]:
    X = X.tocsr()
    out = []
    for i in range(X.shape[0]):
        s, e = X.indptr[i], X.indptr[i + 1]
        data, cols = X.data[s:e], X.indices[s:e]
        order = np.argsort(-data)[: n * 3]
        out.append(dedupe_phrases([str(names[cols[j]]) for j in order], n))
    return out


def global_keywords(X, names: np.ndarray, n: int = 30) -> list[dict]:
    mean = np.asarray(X.mean(axis=0)).ravel()
    df = np.asarray((X > 0).sum(axis=0)).ravel()
    order = np.argsort(-mean)
    picked = dedupe_phrases([str(names[i]) for i in order[: n * 4]], n)
    pos = {str(names[i]): i for i in order[: n * 4]}
    return [{"term": t, "score": round(float(mean[pos[t]]), 5), "docs": int(df[pos[t]])} for t in picked]


def fit_clusters(texts: list[str], X, names: np.ndarray, k_range=range(6, 13), seed: int = 0) -> dict | None:
    n = X.shape[0]
    if n < 100:
        return None
    n_comp = int(min(100, X.shape[1] - 1, n - 1))
    svd = TruncatedSVD(n_components=n_comp, random_state=seed)
    Z = Normalizer(copy=False).fit_transform(svd.fit_transform(X))
    rng = np.random.default_rng(seed)
    sample = rng.choice(n, size=min(2500, n), replace=False)
    scan = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for k in k_range:
            km = KMeans(n_clusters=k, n_init=3, random_state=seed).fit(Z[sample])
            scan.append({"k": int(k), "silhouette": float(silhouette_score(Z[sample], km.labels_)),
                         "inertia": float(km.inertia_)})
        best_k = max(scan, key=lambda s: s["silhouette"])["k"]
        km = KMeans(n_clusters=best_k, n_init=10, random_state=seed).fit(Z)
    labels = km.labels_
    clusters = []
    Xc = X.tocsr()
    for c in range(best_k):
        idx = np.where(labels == c)[0]
        centroid_tfidf = np.asarray(Xc[idx].mean(axis=0)).ravel()
        d = np.linalg.norm(Z[idx] - km.cluster_centers_[c], axis=1)
        clusters.append({"cluster_id": c, "terms": dedupe_phrases(_top_terms(centroid_tfidf, names, 24), 8),
                         "representative_idx": [int(idx[j]) for j in np.argsort(d)[:3]]})
    # 2-D projection for visualisation (PCA of the SVD space)
    pts_idx = rng.choice(n, size=min(1500, n), replace=False)
    P = PCA(n_components=2, random_state=seed).fit_transform(Z)
    return {"svd": svd, "kmeans": km, "labels": labels, "k": best_k, "scan": scan, "clusters": clusters,
            "silhouette": float(next(s["silhouette"] for s in scan if s["k"] == best_k)),
            "points": [{"i": int(i), "x": round(float(P[i, 0]), 4), "y": round(float(P[i, 1]), 4),
                        "cluster": int(labels[i])} for i in pts_idx]}


def assign_clusters(model: dict, X) -> np.ndarray:
    Z = Normalizer(copy=False).fit_transform(model["svd"].transform(X))
    return model["kmeans"].predict(Z)


def cluster_vs_labels(labels: np.ndarray, truth: list[str | None]) -> dict | None:
    m = np.array([t is not None for t in truth])
    if m.sum() < 50:
        return None
    t = np.asarray(truth, dtype=object)[m]
    return {"adjusted_rand": float(adjusted_rand_score(t, labels[m])),
            "nmi": float(normalized_mutual_info_score(t, labels[m])), "n_labeled": int(m.sum())}
