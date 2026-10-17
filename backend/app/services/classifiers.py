"""Supervised text models: sentiment + complaint category.

Leakage control: the TF-IDF vectoriser lives *inside* each sklearn Pipeline, so it is fitted only on training
folds / the training split. Model selection uses 5-fold CV on the training split only; the held-out test split
is touched once, for reporting.
"""
import warnings

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .nlp import analyzer_unigram_bigram

MIN_PER_CLASS = 6
MIN_ROWS = 80


def make_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(analyzer=analyzer_unigram_bigram, min_df=2, max_df=0.95, sublinear_tf=True)


def candidate_models() -> dict:
    return {
        "Logistic Regression": LogisticRegression(C=5.0, max_iter=1000, class_weight="balanced"),
        "Linear SVM": CalibratedClassifierCV(LinearSVC(C=0.5, class_weight="balanced"), cv=3),
        "Majority baseline": DummyClassifier(strategy="most_frequent"),
    }


def _ece(proba: np.ndarray, y_true: np.ndarray, classes: np.ndarray, bins: int = 10) -> float:
    conf = proba.max(1)
    correct = (classes[proba.argmax(1)] == y_true).astype(float)
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            ece += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(ece)


def train_classifier(texts: list[str], labels: list[str], seed: int = 42) -> dict | None:
    """Returns {'pipeline', 'results', 'selected', 'split'(bool test mask over input rows), 'labels'} or None."""
    y = np.asarray(labels, dtype=object)
    counts = {c: int((y == c).sum()) for c in set(labels)}
    keep = np.array([counts[v] >= MIN_PER_CLASS for v in y])
    if keep.sum() < MIN_ROWS or len({v for v, k in zip(y, keep) if k}) < 2:
        return None
    idx = np.where(keep)[0]
    X = np.asarray(texts, dtype=object)
    tr, te = train_test_split(idx, test_size=0.2, random_state=seed, stratify=y[idx])
    classes = np.array(sorted(set(y[idx])))
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)

    results, fitted = [], {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, clf in candidate_models().items():
            pipe = Pipeline([("tfidf", make_vectorizer()), ("clf", clf)])
            cv_f1 = float(cross_val_score(pipe, X[tr], y[tr], cv=cv, scoring="f1_macro").mean())
            pipe.fit(X[tr], y[tr])
            pred = pipe.predict(X[te])
            p, r, f, _ = precision_recall_fscore_support(y[te], pred, labels=classes, average="macro", zero_division=0)
            pc_p, pc_r, pc_f, pc_s = precision_recall_fscore_support(y[te], pred, labels=classes, zero_division=0)
            res = {
                "model_name": name, "accuracy": float(accuracy_score(y[te], pred)),
                "precision_macro": float(p), "recall_macro": float(r), "f1_macro": float(f), "cv_f1_macro": cv_f1,
                "labels": classes.tolist(),
                "confusion": confusion_matrix(y[te], pred, labels=classes).tolist(),
                "per_class": {c: {"precision": float(pc_p[i]), "recall": float(pc_r[i]), "f1": float(pc_f[i]),
                                  "support": int(pc_s[i])} for i, c in enumerate(classes)},
                "n_train": int(len(tr)), "n_test": int(len(te)),
            }
            if hasattr(pipe, "predict_proba") and name != "Majority baseline":
                proba = pipe.predict_proba(X[te])
                res["mean_confidence"] = float(proba.max(1).mean())
                res["ece"] = _ece(proba, y[te], pipe.classes_)
            results.append(res)
            fitted[name] = pipe

    contenders = [r for r in results if r["model_name"] != "Majority baseline"]
    best = max(contenders, key=lambda r: r["cv_f1_macro"])  # chosen on CV (train split), not on the test set
    for r in results:
        r["is_selected"] = r["model_name"] == best["model_name"]
    is_test = np.zeros(len(y), dtype=bool)
    is_test[te] = True
    is_train = np.zeros(len(y), dtype=bool)
    is_train[tr] = True
    return {"pipeline": fitted[best["model_name"]], "results": results, "selected": best["model_name"],
            "is_train": is_train, "is_test": is_test, "labels": classes.tolist()}


def coef_matrix(pipe: Pipeline) -> np.ndarray | None:
    """(n_classes, n_features) linear weights for LR or calibrated LinearSVC."""
    clf = pipe.named_steps["clf"]
    if hasattr(clf, "coef_"):
        return clf.coef_ if clf.coef_.shape[0] > 1 else np.vstack([-clf.coef_[0], clf.coef_[0]])
    if hasattr(clf, "calibrated_classifiers_"):
        return np.mean([cc.estimator.coef_ for cc in clf.calibrated_classifiers_], axis=0)
    return None


def explain(pipe: Pipeline, text: str, target: str, top: int = 6) -> list[dict]:
    """Terms in `text` that pushed the model towards `target` (weight = tf-idf * coefficient).
    This is a statement about the fitted model, not about real-world causes."""
    W = coef_matrix(pipe)
    if W is None:
        return []
    vec = pipe.named_steps["tfidf"]
    classes = list(pipe.named_steps["clf"].classes_)
    if target not in classes:
        return []
    x = vec.transform([text]).tocoo()
    names = vec.get_feature_names_out()
    w = W[classes.index(target)]
    contrib = sorted(((names[j], float(v * w[j])) for j, v in zip(x.col, x.data)), key=lambda t: -t[1])
    return [{"term": t, "weight": round(c, 4)} for t, c in contrib[:top] if c > 0]


def influential_terms(pipe: Pipeline, top: int = 10) -> dict[str, list[dict]]:
    W = coef_matrix(pipe)
    if W is None:
        return {}
    names = pipe.named_steps["tfidf"].get_feature_names_out()
    classes = list(pipe.named_steps["clf"].classes_)
    return {c: [{"term": names[j], "weight": round(float(W[i, j]), 3)} for j in np.argsort(-W[i])[:top]]
            for i, c in enumerate(classes)}


def predict_with_proba(pipe: Pipeline, texts: list[str]):
    proba = pipe.predict_proba(texts)
    classes = np.asarray(pipe.named_steps["clf"].classes_)
    return classes[proba.argmax(1)], proba.max(1), proba, classes
