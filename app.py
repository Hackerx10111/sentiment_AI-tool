"""
Sentiment Analysis Tool
========================
A Flask web application that uses NLP (VADER + optional ML model) to classify
customer reviews as Positive, Negative, or Neutral.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000
"""

import os
import json
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from sentiment_engine import SentimentEngine
from report_generator import generate_report

app = Flask(__name__)
engine = SentimentEngine()


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyse", methods=["POST"])
def analyse():
    """Analyse one or many reviews sent as JSON."""
    data = request.get_json()
    reviews = data.get("reviews", [])

    if not reviews:
        return jsonify({"error": "No reviews provided"}), 400

    results = [engine.predict(r) for r in reviews]
    summary = build_summary(results)

    return jsonify({"results": results, "summary": summary})


@app.route("/api/upload", methods=["POST"])
def upload():
    """Accept a CSV file and analyse every text row."""
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    content = file.read().decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(content))

    reviews = []
    for row in reader:
        if row:
            text = row[0].strip()
            if text and text.lower() not in ("text", "review", "comment"):
                reviews.append(text)

    if not reviews:
        return jsonify({"error": "No text found in CSV"}), 400

    results = [engine.predict(r) for r in reviews]
    summary = build_summary(results)

    return jsonify({"results": results, "summary": summary})


@app.route("/api/report", methods=["POST"])
def report():
    """Generate and return a PDF report for the provided results."""
    data    = request.get_json()
    results = data.get("results", [])
    summary = data.get("summary", {})

    if not results:
        return jsonify({"error": "No results provided"}), 400

    pdf_bytes = generate_report(results, summary)
    filename  = f"sentiment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


# ─── Helpers ───────────────────────────────────────────────────────────────────

def build_summary(results):
    total = len(results)
    counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for r in results:
        counts[r["sentiment"]] += 1
    percentages = {k: round(v / total * 100, 1) if total else 0 for k, v in counts.items()}
    dominant = max(counts, key=counts.get)
    return {
        "total": total,
        "counts": counts,
        "percentages": percentages,
        "dominant": dominant,
    }


# ─── Entry point ───────────────────────────────────────────────────────────────


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
