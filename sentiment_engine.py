"""
sentiment_engine.py
====================
Core NLP pipeline:
  1. VADER  — rule-based, fast, works out-of-the-box (primary model)
  2. Logistic Regression (scikit-learn) — optional trained ML model

VADER is used by default so the tool works immediately without any training data.
If you want to train a custom model, call engine.train(texts, labels) and it will
automatically switch to the ML model for subsequent predictions.
"""

import re
import string
import pickle
import os

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords

# scikit-learn (optional ML layer)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report


# Download required NLTK data on first run
for pkg in ("vader_lexicon", "stopwords", "punkt"):
    try:
        nltk.data.find(f"corpora/{pkg}" if pkg == "stopwords" else f"tokenizers/{pkg}" if pkg == "punkt" else f"sentiment/{pkg}")
    except LookupError:
        nltk.download(pkg, quiet=True)


MODEL_PATH = os.path.join(os.path.dirname(__file__), "data", "ml_model.pkl")


class SentimentEngine:
    """
    Wraps VADER and an optional trained LogisticRegression pipeline.

    Usage
    -----
    engine = SentimentEngine()
    result = engine.predict("The product is amazing!")
    # {'text': '...', 'sentiment': 'Positive', 'confidence': 87, 'scores': {...}}

    # To train a custom ML model:
    engine.train(texts_list, labels_list)  # labels: 'Positive','Negative','Neutral'
    """

    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.ml_model = None
        self._load_model()

    # ── Prediction ────────────────────────────────────────────────────────────

    def predict(self, text: str) -> dict:
        """Return sentiment classification for a single review."""
        cleaned = self._clean(text)

        if self.ml_model:
            return self._ml_predict(text, cleaned)
        return self._vader_predict(text, cleaned)

    def _vader_predict(self, original: str, cleaned: str) -> dict:
        scores = self.vader.polarity_scores(cleaned)
        compound = scores["compound"]

        if compound >= 0.05:
            sentiment = "Positive"
            confidence = min(100, int(50 + compound * 50))
        elif compound <= -0.05:
            sentiment = "Negative"
            confidence = min(100, int(50 + abs(compound) * 50))
        else:
            sentiment = "Neutral"
            confidence = max(50, int(100 - abs(compound) * 200))

        return {
            "text": original,
            "sentiment": sentiment,
            "confidence": confidence,
            "scores": {
                "positive": round(scores["pos"], 3),
                "negative": round(scores["neg"], 3),
                "neutral": round(scores["neu"], 3),
                "compound": round(scores["compound"], 3),
            },
            "model": "VADER",
        }

    def _ml_predict(self, original: str, cleaned: str) -> dict:
        proba = self.ml_model.predict_proba([cleaned])[0]
        classes = self.ml_model.classes_
        idx = proba.argmax()
        sentiment = classes[idx]
        confidence = int(proba[idx] * 100)

        return {
            "text": original,
            "sentiment": sentiment,
            "confidence": confidence,
            "scores": {c: round(float(p), 3) for c, p in zip(classes, proba)},
            "model": "LogisticRegression",
        }

    # ── Training (optional) ───────────────────────────────────────────────────

    def train(self, texts: list, labels: list) -> str:
        """
        Train a Logistic Regression model on labelled data.

        Parameters
        ----------
        texts  : list of raw review strings
        labels : list of 'Positive', 'Negative', or 'Neutral'

        Returns
        -------
        Classification report string
        """
        from sklearn.model_selection import train_test_split

        cleaned = [self._clean(t) for t in texts]
        X_train, X_test, y_train, y_test = train_test_split(
            cleaned, labels, test_size=0.2, random_state=42, stratify=labels
        )

        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced")),
        ])
        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        report = classification_report(y_test, y_pred, zero_division=0)

        self.ml_model = pipeline
        self._save_model()
        return report

    # ── Text cleaning ─────────────────────────────────────────────────────────

    def _clean(self, text: str) -> str:
        """Lowercase, remove URLs, punctuation, extra whitespace."""
        text = text.lower()
        text = re.sub(r"http\S+|www\S+", "", text)       # remove URLs
        text = re.sub(r"<.*?>", "", text)                  # remove HTML tags
        text = re.sub(r"[^a-z0-9\s]", " ", text)          # remove punctuation
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ── Model persistence ─────────────────────────────────────────────────────

    def _save_model(self):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.ml_model, f)
        print(f"[Engine] ML model saved to {MODEL_PATH}")

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                self.ml_model = pickle.load(f)
            print(f"[Engine] Loaded ML model from {MODEL_PATH}")
        else:
            print("[Engine] No saved ML model found — using VADER.")
