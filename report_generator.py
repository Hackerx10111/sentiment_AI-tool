"""
report_generator.py
====================
Generates a professional PDF sentiment analysis report using ReportLab.

Called by app.py when the user clicks "Download PDF Report".
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF


# ── Brand colours ──────────────────────────────────────────────────────────────
C_POS    = colors.HexColor("#1D9E75")
C_NEG    = colors.HexColor("#D85A30")
C_NEU    = colors.HexColor("#BA7517")
C_DARK   = colors.HexColor("#1a1a18")
C_BLUE   = colors.HexColor("#185FA5")
C_LIGHT  = colors.HexColor("#F5F5F3")
C_BORDER = colors.HexColor("#E0DFD8")
C_WHITE  = colors.white


def generate_report(results: list, summary: dict) -> bytes:
    """
    Build and return a PDF report as bytes.

    Parameters
    ----------
    results : list of dicts  [{text, sentiment, confidence, scores, model}, ...]
    summary : dict           {total, counts, percentages, dominant}
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title="Sentiment Analysis Report",
        author="Sentiment Analysis Tool",
    )

    styles  = _build_styles()
    story   = []

    # ── Cover / header block ─────────────────────────────────────────────────
    story += _header_block(styles, summary)
    story.append(Spacer(1, 0.4*cm))
    story += _summary_cards(summary)
    story.append(Spacer(1, 0.5*cm))

    # ── Charts ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Visualisations", styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=10))
    story += _charts_row(summary)
    story.append(Spacer(1, 0.5*cm))

    # ── Insight ───────────────────────────────────────────────────────────────
    story += _insight_block(styles, summary)
    story.append(Spacer(1, 0.5*cm))

    # ── Review breakdown table ────────────────────────────────────────────────
    story.append(Paragraph("Review Breakdown", styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=10))
    story += _reviews_table(styles, results)

    # ── Footer note ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph(
        f"Report generated on {datetime.now().strftime('%d %B %Y at %H:%M')} &nbsp;|&nbsp; "
        f"Model: {results[0].get('model', 'VADER') if results else 'VADER'} &nbsp;|&nbsp; "
        f"Sentiment Analysis Tool",
        styles["FooterNote"]
    ))

    doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    buffer.seek(0)
    return buffer.read()


# ── Page number callback ───────────────────────────────────────────────────────
def _add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#999999"))
    canvas.drawRightString(A4[0] - 2*cm, 1.2*cm, f"Page {doc.page}")
    canvas.restoreState()


# ── Styles ─────────────────────────────────────────────────────────────────────
def _build_styles():
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "ReportTitle", parent=base["Title"],
            fontSize=22, textColor=C_WHITE, spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle", parent=base["Normal"],
            fontSize=10, textColor=colors.HexColor("#cccccc"),
        ),
        "SectionTitle": ParagraphStyle(
            "SectionTitle", parent=base["Normal"],
            fontSize=12, fontName="Helvetica-Bold",
            textColor=C_DARK, spaceBefore=6, spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "Body", parent=base["Normal"],
            fontSize=10, leading=14, textColor=C_DARK,
        ),
        "InsightBody": ParagraphStyle(
            "InsightBody", parent=base["Normal"],
            fontSize=10, leading=15, textColor=colors.HexColor("#0c447c"),
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader", parent=base["Normal"],
            fontSize=9, fontName="Helvetica-Bold", textColor=C_WHITE,
        ),
        "TableCell": ParagraphStyle(
            "TableCell", parent=base["Normal"],
            fontSize=8, leading=12, textColor=C_DARK,
        ),
        "FooterNote": ParagraphStyle(
            "FooterNote", parent=base["Normal"],
            fontSize=8, textColor=colors.HexColor("#aaaaaa"), alignment=1,
        ),
    }


# ── Header block ───────────────────────────────────────────────────────────────
def _header_block(styles, summary):
    now = datetime.now().strftime("%d %B %Y")

    # Dark banner via a 1-row table
    header_table = Table(
        [[
            Paragraph("Sentiment Analysis Report", styles["Title"]),
            Paragraph(f"Generated: {now}<br/>Total reviews: {summary['total']}", styles["Subtitle"]),
        ]],
        colWidths=["65%", "35%"],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), C_DARK),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",   (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 16),
        ("ALIGN",        (1, 0), (1, 0),   "RIGHT"),
        ("ROUNDEDCORNERS", [6]),
    ]))
    return [header_table, Spacer(1, 0.3*cm)]


# ── Summary metric cards ────────────────────────────────────────────────────────
def _summary_cards(summary):
    c = summary["counts"]
    p = summary["percentages"]
    total = summary["total"]

    def card(label, value, pct, bg, txt_color):
        inner = Table(
            [[Paragraph(str(value), ParagraphStyle("cv", fontSize=26, fontName="Helvetica-Bold", textColor=txt_color, alignment=1))],
             [Paragraph(label,      ParagraphStyle("cl", fontSize=9,  textColor=txt_color, alignment=1))],
             [Paragraph(f"{pct}%",  ParagraphStyle("cp", fontSize=9,  textColor=txt_color, alignment=1, fontName="Helvetica-Bold"))]],
            colWidths=["100%"],
        )
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("ROUNDEDCORNERS",[6]),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return inner

    row = Table(
        [[
            card("Positive 😊", c["Positive"], p["Positive"], colors.HexColor("#E1F5EE"), C_POS),
            card("Negative 😠", c["Negative"], p["Negative"], colors.HexColor("#FAECE7"), C_NEG),
            card("Neutral 😐",  c["Neutral"],  p["Neutral"],  colors.HexColor("#FAEEDA"), C_NEU),
            card("Total",       total,         100,           C_LIGHT,                   C_DARK),
        ]],
        colWidths=["24%", "24%", "24%", "24%"],
        hAlign="CENTER",
    )
    row.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [row]


# ── Charts row ─────────────────────────────────────────────────────────────────
def _charts_row(summary):
    c = summary["counts"]
    pos, neg, neu = c["Positive"], c["Negative"], c["Neutral"]

    pie   = _build_pie(pos, neg, neu)
    bar   = _build_bar(pos, neg, neu)

    row = Table(
        [[pie, bar]],
        colWidths=["45%", "55%"],
    )
    row.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [row]


def _build_pie(pos, neg, neu):
    total = pos + neg + neu or 1
    d = Drawing(220, 180)

    pie = Pie()
    pie.x, pie.y = 20, 20
    pie.width = pie.height = 130
    pie.data   = [pos, neg, neu]
    pie.labels = [
        f"Positive\n{round(pos/total*100)}%",
        f"Negative\n{round(neg/total*100)}%",
        f"Neutral\n{round(neu/total*100)}%",
    ]
    pie.slices[0].fillColor = C_POS
    pie.slices[1].fillColor = C_NEG
    pie.slices[2].fillColor = C_NEU
    pie.slices.strokeColor  = C_WHITE
    pie.slices.strokeWidth  = 1.5
    pie.simpleLabels        = False
    pie.sideLabels          = True
    pie.sideLabelsOffset    = 0.08

    d.add(pie)
    return d


def _build_bar(pos, neg, neu):
    d = Drawing(280, 180)

    bc = VerticalBarChart()
    bc.x, bc.y    = 30, 20
    bc.width      = 220
    bc.height     = 130
    bc.data       = [[pos, neg, neu]]
    bc.categoryAxis.categoryNames = ["Positive", "Negative", "Neutral"]
    bc.bars[0].fillColor = C_POS

    # Individual bar colours via strokeColor workaround
    bc.bars[0].fillColor   = C_POS
    bc.data                = [[pos], [neg], [neu]]
    bc.bars[0].fillColor   = C_POS
    bc.bars[1].fillColor   = C_NEG
    bc.bars[2].fillColor   = C_NEU
    bc.categoryAxis.categoryNames = [""]   # single group
    bc.groupSpacing        = 5
    bc.barSpacing          = 4
    bc.valueAxis.valueMin  = 0
    bc.valueAxis.valueStep = max(1, max(pos, neg, neu) // 5)
    bc.valueAxis.gridStrokeColor = colors.HexColor("#eeeeee")
    bc.strokeColor         = None
    bc.categoryAxis.strokeColor = C_BORDER
    bc.valueAxis.strokeColor    = C_BORDER

    # X labels manually
    labels_y = 10
    for i, (label, val) in enumerate(zip(["Positive", "Negative", "Neutral"], [pos, neg, neu])):
        x = bc.x + i * (bc.width / 3) + (bc.width / 6)
        d.add(String(x, labels_y, label, fontSize=8, textAnchor="middle",
                     fillColor=colors.HexColor("#555555")))

    d.add(bc)
    return d


# ── Insight block ──────────────────────────────────────────────────────────────
def _insight_block(styles, summary):
    p = summary["percentages"]
    c = summary["counts"]
    total = summary["total"]
    dominant = summary["dominant"]

    if p["Positive"] > 60:
        tone = "Overall sentiment is <b>positive</b> — customers are satisfied with the product or service."
    elif p["Negative"] > 40:
        tone = "Overall sentiment is <b>concerning</b> — a high proportion of negative reviews were detected."
    else:
        tone = "Sentiment is <b>mixed</b> — no single emotion strongly dominates customer feedback."

    tip = (
        "Consider reviewing negative feedback to identify recurring pain points and prioritise improvements."
        if c["Negative"] > 0
        else "Excellent! Customers are overwhelmingly positive — maintain current quality standards."
    )

    insight_text = (
        f"{tone}<br/><br/>"
        f"Out of <b>{total}</b> reviews analysed: "
        f"<b>{p['Positive']}%</b> positive, "
        f"<b>{p['Negative']}%</b> negative, "
        f"<b>{p['Neutral']}%</b> neutral.<br/><br/>"
        f"<b>Recommendation:</b> {tip}"
    )

    box = Table(
        [[Paragraph("Key Insight", ParagraphStyle("ih", fontSize=11, fontName="Helvetica-Bold", textColor=C_BLUE, spaceAfter=4)),],
         [Paragraph(insight_text, styles["InsightBody"])]],
        colWidths=["100%"],
    )
    box.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#EEF5FF")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS",[6]),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#B5D4F4")),
    ]))
    return [Paragraph("Insights & Recommendations", styles["SectionTitle"]),
            HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=10),
            box]


# ── Reviews table ──────────────────────────────────────────────────────────────
def _reviews_table(styles, results):
    if not results:
        return [Paragraph("No reviews to display.", styles["Body"])]

    header = [
        Paragraph("#",           styles["TableHeader"]),
        Paragraph("Review Text", styles["TableHeader"]),
        Paragraph("Sentiment",   styles["TableHeader"]),
        Paragraph("Confidence",  styles["TableHeader"]),
        Paragraph("Model",       styles["TableHeader"]),
    ]
    rows = [header]

    sentiment_colours = {
        "Positive": (colors.HexColor("#E1F5EE"), C_POS),
        "Negative": (colors.HexColor("#FAECE7"), C_NEG),
        "Neutral":  (colors.HexColor("#FAEEDA"), C_NEU),
    }

    for i, r in enumerate(results, 1):
        sentiment = r.get("sentiment", "Neutral")
        bg, fg    = sentiment_colours.get(sentiment, (C_LIGHT, C_DARK))
        emoji     = {"Positive": "😊", "Negative": "😠", "Neutral": "😐"}.get(sentiment, "")

        # Truncate very long reviews
        text = r.get("text", "")
        if len(text) > 200:
            text = text[:197] + "…"

        rows.append([
            Paragraph(str(i),                  styles["TableCell"]),
            Paragraph(text,                    styles["TableCell"]),
            Paragraph(f"{emoji} {sentiment}", ParagraphStyle("sc", fontSize=8, textColor=fg, fontName="Helvetica-Bold")),
            Paragraph(f"{r.get('confidence', '—')}%", styles["TableCell"]),
            Paragraph(r.get("model", "VADER"), styles["TableCell"]),
        ])

    table = Table(rows, colWidths=["5%", "57%", "15%", "12%", "11%"], repeatRows=1)

    # Base style
    ts = TableStyle([
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0),  C_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("TOPPADDING",    (0, 0), (-1, 0),  8),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  8),
        # Body rows
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("TOPPADDING",    (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
    ])

    # Colour the sentiment column cells
    for i, r in enumerate(results, 1):
        sentiment = r.get("sentiment", "Neutral")
        bg, _     = sentiment_colours.get(sentiment, (C_LIGHT, C_DARK))
        ts.add("BACKGROUND", (2, i), (2, i), bg)

    table.setStyle(ts)
    return [table]
