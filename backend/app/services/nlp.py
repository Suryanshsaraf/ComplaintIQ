"""Text preprocessing shared by every NLP model (no external corpora needed).

Design notes
* Negations (not, no, never, n't, without, ...) are deliberately KEPT out of the stop-word list because
  "not working" and "working" must stay distinguishable. Bigrams in the vectorizer then capture "not working".
* Contractions are expanded first ("doesn't" -> "does not") so negation survives tokenisation.
"""
import re

CONTRACTIONS = [
    (r"\bwon't\b", "will not"), (r"\bcan't\b", "can not"), (r"\bcannot\b", "can not"),
    (r"n't\b", " not"), (r"'re\b", " are"), (r"'ve\b", " have"), (r"'ll\b", " will"),
    (r"'m\b", " am"), (r"'d\b", " would"), (r"'s\b", ""),
]

NEGATIONS = {"not", "no", "never", "nor", "without", "none", "nothing", "nobody", "neither", "hardly"}

_STOP = """a about above after again against all am an and any are as at be because been before being below between both
but by can did do does doing down during each few for from further had has have having he her here hers herself him
himself his how i if in into is it its itself just me more most my myself of off on once only or other our ours
ourselves out over own same she should so some such than that the their theirs them themselves then there these they
this those through to too under until up very was we were what when where which while who whom why will with would you
your yours yourself yourselves also get got one us""".split()
STOPWORDS = frozenset(w for w in _STOP if w not in NEGATIONS)

_URL = re.compile(r"https?://\S+|www\.\S+")
_EMAIL = re.compile(r"\S+@\S+\.\S+")
_NONALPHA = re.compile(r"[^a-z\s]")
_WS = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Lower-case, expand contractions, strip URLs/emails/digits/punctuation."""
    t = (text or "").lower().replace("’", "'")
    t = _URL.sub(" ", t)
    t = _EMAIL.sub(" ", t)
    for pat, rep in CONTRACTIONS:
        t = re.sub(pat, rep, t)
    t = _NONALPHA.sub(" ", t)
    return _WS.sub(" ", t).strip()


def tokenize(text: str) -> list[str]:
    """Clean, split and drop stop-words / 1-2 character tokens (negations are preserved)."""
    return [w for w in clean_text(text).split() if w not in STOPWORDS and (len(w) > 2 or w in NEGATIONS)]


def analyzer_unigram_bigram(text: str) -> list[str]:
    """Analyzer for TfidfVectorizer: unigrams + bigrams over the filtered token stream."""
    toks = tokenize(text)
    return toks + [f"{a} {b}" for a, b in zip(toks, toks[1:])]
