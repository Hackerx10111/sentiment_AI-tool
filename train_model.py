"""
train_model.py
==============
Optional script to train a custom Logistic Regression sentiment model
on your own labelled data instead of using VADER.

Usage
-----
1. Prepare a CSV file with two columns: text, label
   label must be one of: Positive, Negative, Neutral

2. Run:
   python train_model.py --data path/to/your_data.csv

The trained model is saved to data/ml_model.pkl and will be
automatically picked up by the Flask app on next start.
"""

import argparse
import pandas as pd
from sentiment_engine import SentimentEngine


def main():
    parser = argparse.ArgumentParser(description="Train a custom sentiment model")
    parser.add_argument(
        "--data",
        default="data/sample_reviews.csv",
        help="Path to CSV file with columns: text, label"
    )
    args = parser.parse_args()

    print(f"Loading data from: {args.data}")
    df = pd.read_csv(args.data)

    # Support both labelled CSVs and auto-labelling via VADER for demo purposes
    if "label" not in df.columns:
        print("No 'label' column found — auto-labelling with VADER for demo training…")
        engine_tmp = SentimentEngine()
        df["label"] = df["text"].apply(lambda t: engine_tmp.predict(t)["sentiment"])

    df = df.dropna(subset=["text", "label"])
    texts  = df["text"].tolist()
    labels = df["label"].tolist()

    print(f"Training on {len(texts)} samples…")
    engine = SentimentEngine()
    report = engine.train(texts, labels)

    print("\n── Classification Report ──")
    print(report)
    print("\n✅ Model saved! Restart the Flask app to use it.")


if __name__ == "__main__":
    main()
