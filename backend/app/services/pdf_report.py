import io
import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models.schemas import AnalysisResult

_FONT = "Helvetica"
for path in ("C:/Windows/Fonts/Nirmala.ttf", "C:/Windows/Fonts/NirmalaUI.ttf",
             "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
             "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
             "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc"):
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont("UniFont", path))
            _FONT = "UniFont"
            break
        except Exception:  # noqa: BLE001
            continue


def _p(text: str, style) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def build_pdf(r: AnalysisResult, case_id: str, generated: datetime, raw_text: str | None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                            title="Scam Shield incident report")
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontName=_FONT, fontSize=10, leading=14)
    small = ParagraphStyle("s", parent=body, fontSize=8.5, leading=11)
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontName=_FONT, fontSize=18, alignment=0)
    h2 = ParagraphStyle("h2", parent=body, fontName=_FONT, fontSize=12, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#0E6B7A"))
    el = [_p("Scam Shield - Incident Evidence Report", h1)]
    meta = [["Case ID", case_id], ["Generated", generated.strftime("%d %b %Y, %H:%M UTC")],
            ["Verdict", f"{r.verdict} (risk {r.risk_score}/100)"], ["Scam type", r.scam_type.replace("_", " ")],
            ["Language", r.language], ["Source", r.source]]
    t = Table([[_p(a, body), _p(b, body)] for a, b in meta], colWidths=[35 * mm, 135 * mm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF3F4"))]))
    el += [t, Spacer(1, 6), _p("Summary", h2), _p(r.explanation.en, body)]
    if r.explanation.hi:
        el.append(_p(r.explanation.hi, body))
    el.append(_p("Signal timeline", h2))
    if r.signals:
        rows = [[_p("#", small), _p("Signal", small), _p("Quote from the message / call", small), _p("Weight", small)]]
        for i, s in enumerate(r.signals, 1):
            rows.append([_p(str(i), small), _p(s.type.replace("_", " "), small), _p(f"\"{s.evidence}\"", small), _p(str(s.weight), small)])
        st = Table(rows, colWidths=[8 * mm, 45 * mm, 100 * mm, 17 * mm], repeatRows=1)
        st.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF3F4")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        el.append(st)
    else:
        el.append(_p("No warning signs were recorded.", body))
    e = r.entities
    el.append(_p("Numbers, UPI IDs and links found", h2))
    for label, vals in [("Phone numbers", e.phones), ("UPI IDs", e.upi_ids), ("Links", e.urls), ("Apps", e.apps), ("Amounts", e.amounts)]:
        el.append(_p(f"{label}: " + (", ".join(vals) if vals else "none"), body))
    if r.blocklist_hits:
        el.append(_p("Already reported by others: " + ", ".join(f"{h.value} ({h.reports} reports)" for h in r.blocklist_hits), body))
    if raw_text:
        el.append(_p("Transcript / message (saved with your permission)", h2))
        el.append(_p(raw_text[:6000], small))
    box = Table([[_p("WHAT TO DO NOW", ParagraphStyle("bx", parent=body, fontName=_FONT, fontSize=11, textColor=colors.white))],
                 [_p("1. Call 1930 (national cyber crime helpline) immediately. The first hour matters most if money was sent.\n"
                     "2. Report at cybercrime.gov.in and keep the complaint number.\n"
                     "3. Tell your bank to block / freeze the transaction and your cards.\n"
                     "4. Do not delete messages, screenshots or call logs. They are evidence.\n"
                     "5. Do not send more money, even if they promise a refund.", body)]], colWidths=[170 * mm])
    box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#B3171C")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#B3171C")),
                             ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    el += [Spacer(1, 10), box]

    def footer(c, d):
        c.saveState()
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.grey)
        c.drawString(18 * mm, 10 * mm, "Generated aid, not an FIR.")
        c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Case {case_id[:8]} - page {d.page}")
        c.restoreState()

    doc.build(el, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
