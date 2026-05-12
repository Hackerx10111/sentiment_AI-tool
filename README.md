# 🧠 Sentiment Analysis Tool

A full-stack web application that classifies customer reviews as **Positive 😊**, **Negative 😠**, or **Neutral 😐** using Natural Language Processing (NLP).

Built with **Python**, **Flask**, **NLTK (VADER)**, **scikit-learn**, **Chart.js**.

---

## 📁 Project Structure

```
sentiment_tool/
├── app.py                  # Flask web server + API routes
├── sentiment_engine.py     # NLP engine (VADER + Logistic Regression)
├── train_model.py          # Optional: train a custom ML model
├── requirements.txt        # Python dependencies
├── data/
│   ├── sample_reviews.csv  # Sample data to test with
│   └── ml_model.pkl        # Saved ML model (created after training)
├── templates/
│   └── index.html          # Main dashboard page
└── static/
    ├── css/
    │   └── style.css       # Stylesheet
    └── js/
        └── app.js          # Frontend logic + Chart.js charts
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.9 or higher
- pip

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```

### 5. Open in your browser
```
http://localhost:5000
```

---

## 🚀 Features

| Feature | Description |
|---|---|
| **Single review analysis** | Type or paste any review and classify it instantly |
| **Bulk analysis** | Paste multiple reviews (one per line) and analyse all at once |
| **CSV upload** | Upload a `.csv` file of reviews for batch processing |
| **Sample data** | Load 15 pre-built sample reviews to test immediately |
| **Bar chart** | Compare counts of positive / negative / neutral reviews |
| **Pie chart** | See percentage distribution as a doughnut chart |
| **Trend chart** | Track how sentiment changes across analysis batches |
| **Filterable list** | Filter classified reviews by sentiment type |
| **Key insight** | Auto-generated summary of overall customer sentiment |

---

## 🧪 How It Works

### Step 1 — Text Cleaning
- Converts text to lowercase
- Removes URLs, HTML tags, and punctuation
- Strips extra whitespace

### Step 2 — Sentiment Classification
**Default model: VADER** (Valence Aware Dictionary and sEntiment Reasoner)
- Rule-based NLP model, works without training data
- Returns compound score from -1 (most negative) to +1 (most positive)
- Compound ≥ 0.05 → Positive | ≤ -0.05 → Negative | between → Neutral

**Optional: Logistic Regression** (scikit-learn)
- TF-IDF vectorisation + Logistic Regression classifier
- Train on your own labelled data for higher accuracy

### Step 3 — Results & Visualisation
- Counts and percentages per sentiment
- Three interactive Chart.js charts
- Filterable review list with confidence scores

---

## 🏋️ Training a Custom ML Model (Optional)

If you have labelled review data, you can train a custom model:

### Prepare a CSV with two columns:
```csv
text,label
"The service was amazing!",Positive
"Delivery was too slow.",Negative
"The product is okay.",Neutral
```

### Run the training script:
```bash
python train_model.py --data path/to/your_labelled_data.csv
```

The model is saved to `data/ml_model.pkl` and automatically loaded next time you start the app.

---

## 🌍 Real-World Use Cases

- **Retail** — Analyse product reviews to improve offerings (e.g. Takealot, Amazon)
- **Banking** — Monitor customer complaints to improve service (e.g. Nedbank)
- **Telecom** — Track social media sentiment (e.g. MTN, Vodacom)
- **E-commerce** — Identify pain points in post-purchase feedback

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| Flask | Web framework |
| NLTK + VADER | Rule-based sentiment analysis |
| scikit-learn | ML model (TF-IDF + Logistic Regression) |
| pandas | Data loading and CSV handling |
| numpy | Numerical operations |
| Chart.js (CDN) | Interactive charts in the browser |

---

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves the dashboard |
| POST | `/api/analyse` | Analyse JSON list of reviews |
| POST | `/api/upload` | Upload and analyse a CSV file |

### Example API call:
```bash
curl -X POST http://localhost:5000/api/analyse \
  -H "Content-Type: application/json" \
  -d '{"reviews": ["Great product!", "Terrible service."]}'
```

---

## 📄 Licence
MIT — free to use, modify, and distribute for academic and commercial projects.
