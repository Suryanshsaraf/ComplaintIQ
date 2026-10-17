from app.services.nlp import analyzer_unigram_bigram, clean_text, tokenize


def test_clean_text_strips_noise():
    assert clean_text("Visit https://x.com or mail a@b.com! Order #123") == "visit or mail order"


def test_negations_preserved():
    toks = tokenize("The app doesn't work and I can't log in, never again")
    assert "not" in toks and "never" in toks
    assert "the" not in toks and "and" not in toks


def test_bigrams_capture_negation():
    assert "not working" in analyzer_unigram_bigram("It is not working")
