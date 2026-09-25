# services/pdf_report_service.py
#
# Server-side PDF generation for tenant-dashboard reports, using reportlab
# (pure Python, no native/browser dependency — safe to run on the same VPS
# as the API, unlike a headless-Chromium approach).
#
# Why this exists alongside the dashboard's "Print" button (browser
# print-to-PDF): a browser's print pipeline cannot guarantee A4 sizing,
# reliably repeat table headers across pages, or draw true running
# header/footer content — it renders whatever CSS happens to apply at
# print time, which is exactly what caused the "no column names" / "not
# all rows fit" / stray scrollbar bugs before Print was fixed. This
# produces an actual PDF document: fixed A4 portrait, a letterhead + footer
# drawn once and repeated identically on every page, a table header row
# that reflows onto each new page, and text that wraps inside its own
# column instead of ever overflowing the page.

from __future__ import annotations

import base64
from datetime import datetime
from io import BytesIO
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.concurrency import run_in_threadpool
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_PAGE_SIZE = A4
_MARGIN = 16 * mm
_HEADER_H = 24 * mm
_FOOTER_H = 12 * mm

_NAVY = colors.HexColor("#0f172a")
_MUTED = colors.HexColor("#64748b")
_ZEBRA = colors.HexColor("#f8fafc")
_RULE = colors.HexColor("#e2e8f0")
_ACCENT = colors.HexColor("#4f46e5")

_body_style = ParagraphStyle("body", fontName="Helvetica", fontSize=8, leading=10, textColor=_NAVY)
_body_muted_style = ParagraphStyle("body_muted", parent=_body_style, textColor=_MUTED)
_body_right_style = ParagraphStyle("body_right", parent=_body_style, alignment=2)
_header_cell_style = ParagraphStyle(
    "header_cell", fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=_NAVY,
)
_header_cell_right_style = ParagraphStyle("header_cell_right", parent=_header_cell_style, alignment=2)
_section_title_style = ParagraphStyle(
    "section_title", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=_NAVY,
    spaceBefore=10, spaceAfter=6,
)
_kpi_label_style = ParagraphStyle("kpi_label", fontName="Helvetica", fontSize=7, textColor=_MUTED)
_kpi_value_style = ParagraphStyle("kpi_value", fontName="Helvetica-Bold", fontSize=13, textColor=_NAVY)


def _esc(value) -> str:
    text = "" if value is None else str(value)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class _NumberedCanvas(pdfcanvas.Canvas):
    """Defers 'Page X of Y' until every page is known — the standard
    reportlab two-pass recipe (the total page count doesn't exist until
    the whole flowable story has been laid out)."""

    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_number(total)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def _draw_page_number(self, total: int) -> None:
        self.setFont("Helvetica", 7)
        self.setFillColor(_MUTED)
        self.drawRightString(
            _PAGE_SIZE[0] - _MARGIN, _FOOTER_H - 5 * mm, f"Page {self._pageNumber} of {total}",
        )


def _page_decorator(
    *, business_name: str, logo_bytes: bytes | None, branch_line: str,
    report_title: str, generated_at: str,
):
    def _decorate(canvas_obj: pdfcanvas.Canvas, _doc) -> None:
        canvas_obj.saveState()
        width, height = _PAGE_SIZE
        top_y = height - _MARGIN
        x = _MARGIN

        if logo_bytes:
            try:
                img = ImageReader(BytesIO(logo_bytes))
                size = 15 * mm
                canvas_obj.drawImage(
                    img, x, top_y - size, width=size, height=size,
                    preserveAspectRatio=True, mask="auto",
                )
                x += size + 4 * mm
            except Exception:
                pass  # a damaged/unreadable logo file must never break report generation

        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.setFillColor(_NAVY)
        canvas_obj.drawString(x, top_y - 6 * mm, business_name or "My Business")
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(_MUTED)
        canvas_obj.drawString(x, top_y - 11 * mm, branch_line or "All branches")

        canvas_obj.setFont("Helvetica-Bold", 11)
        canvas_obj.setFillColor(_NAVY)
        canvas_obj.drawRightString(width - _MARGIN, top_y - 6 * mm, report_title)
        canvas_obj.setFont("Helvetica", 7.5)
        canvas_obj.setFillColor(_MUTED)
        canvas_obj.drawRightString(width - _MARGIN, top_y - 11 * mm, generated_at)

        canvas_obj.setStrokeColor(_NAVY)
        canvas_obj.setLineWidth(1.1)
        canvas_obj.line(_MARGIN, top_y - 14.5 * mm, width - _MARGIN, top_y - 14.5 * mm)

        canvas_obj.setStrokeColor(_RULE)
        canvas_obj.setLineWidth(0.6)
        canvas_obj.line(_MARGIN, _FOOTER_H, width - _MARGIN, _FOOTER_H)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(_MUTED)
        canvas_obj.drawCentredString(
            width / 2, _FOOTER_H - 5 * mm,
            "Storixx · developed by apkaysoftware.com · 03487457766",
        )
        canvas_obj.restoreState()

    return _decorate


def _cell(value, *, numeric: bool = False, muted: bool = False) -> Paragraph:
    style = _body_right_style if numeric else (_body_muted_style if muted else _body_style)
    return Paragraph(_esc(value), style)


def kpi_row(items: list[tuple[str, str]]) -> Table:
    """A row of boxed KPI tiles (label + big value) — e.g. Total Sales,
    Revenue — for the top of a report, matching the dashboard's own card
    layout instead of burying totals inside a plain table."""
    available = _PAGE_SIZE[0] - 2 * _MARGIN
    col_width = available / len(items)
    # Each tile is its own tiny 2-row table (label, value) so the outer
    # row can give it a border/box; wrap all tiles in one outer Table.
    tiles = []
    for label, value in items:
        tile = Table([[Paragraph(_esc(label), _kpi_label_style)],
                       [Paragraph(_esc(value), _kpi_value_style)]], colWidths=[col_width - 6])
        tile.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, _RULE),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        tiles.append(tile)
    outer = Table([tiles], colWidths=[col_width] * len(items))
    outer.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return outer


def data_table(
    columns: list[str], rows: list[list], *,
    numeric_cols: set[int] | None = None,
    col_fractions: list[float] | None = None,
    totals: list | None = None,
) -> Table:
    """One report table: bold header row (repeats on every page via
    repeatRows), alternating row shading, wrapped text cells so nothing is
    ever clipped or forces a horizontal overflow."""
    numeric_cols = numeric_cols or set()
    available = _PAGE_SIZE[0] - 2 * _MARGIN
    if col_fractions:
        col_widths = [available * f for f in col_fractions]
    else:
        col_widths = [available / len(columns)] * len(columns)

    header = [
        Paragraph(_esc(c).upper(), _header_cell_right_style if i in numeric_cols else _header_cell_style)
        for i, c in enumerate(columns)
    ]
    body = [
        [_cell(v, numeric=(i in numeric_cols)) for i, v in enumerate(row)]
        for row in rows
    ]
    data = [header] + body
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, _NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, _RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for row_idx in range(1, len(data), 2):
        style.append(("BACKGROUND", (0, row_idx), (-1, row_idx), _ZEBRA))
    if totals is not None:
        totals_cells = [
            Paragraph(f"<b>{_esc(v)}</b>", _body_right_style if i in numeric_cols else _body_style)
            for i, v in enumerate(totals)
        ]
        data.append(totals_cells)
        style.append(("LINEABOVE", (0, -1), (-1, -1), 1.2, _NAVY))
        style.append(("BACKGROUND", (0, -1), (-1, -1), colors.white))

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style))
    return table


def section_title(text: str) -> Paragraph:
    return Paragraph(_esc(text), _section_title_style)


async def get_branding(
    db: AsyncSession, tenant_id: UUID, branch_id: UUID | None,
) -> tuple[str, bytes | None, str, str]:
    """(business_name, logo_bytes, branch_line, currency) for the letterhead
    and money columns — one query, reused by every PDF endpoint so they
    never drift from each other or from the dashboard's own on-screen
    letterhead."""
    from models.branch import Branch
    from models.business import Business
    from services.pos_sync_service import _logo_base64

    business = await db.scalar(
        select(Business).where(Business.tenant_id == tenant_id, Business.deleted_at.is_(None))
    )
    business_name = business.name if business else "My Business"
    logo_b64 = _logo_base64(business.logo_path) if business else None
    logo_bytes = base64.b64decode(logo_b64) if logo_b64 else None
    currency = business.currency if business else "Rs."

    branch_line = "All branches"
    if branch_id is not None:
        branch_name = await db.scalar(select(Branch.name).where(Branch.id == branch_id))
        if branch_name:
            branch_line = branch_name

    return business_name, logo_bytes, branch_line, currency


async def build_pdf(
    *, business_name: str, logo_bytes: bytes | None, branch_line: str,
    report_title: str, flowables: list, subtitle: str | None = None,
) -> bytes:
    """Assembles any list of flowables (data_table()/kpi_row()/section_title()
    output, Spacer, etc.) into a finished A4-portrait PDF with the standard
    letterhead, footer, and page numbers on every page.

    [subtitle], when given, replaces the "Generated <date>" line under the
    report title — e.g. a date-range label reads better there than a print
    timestamp for a period-scoped report (sales). Keep [report_title] itself
    short and plain (no " — " period baked in) either way.

    doc.build() is synchronous, CPU-bound layout/pagination work — for a
    large report it can take a noticeable fraction of a second, which would
    otherwise block this single-threaded event loop and stall every other
    concurrent request on the same worker. Offloaded to a thread so it
    doesn't.
    """
    buf = BytesIO()
    generated_at = subtitle or ("Generated " + datetime.now().strftime("%d %b %Y, %I:%M %p"))
    doc = SimpleDocTemplate(
        buf, pagesize=_PAGE_SIZE,
        leftMargin=_MARGIN, rightMargin=_MARGIN,
        topMargin=_MARGIN + _HEADER_H, bottomMargin=_MARGIN + _FOOTER_H,
        title=report_title,
    )
    decorate = _page_decorator(
        business_name=business_name, logo_bytes=logo_bytes, branch_line=branch_line,
        report_title=report_title, generated_at=generated_at,
    )
    await run_in_threadpool(
        doc.build,
        flowables or [Paragraph("No data for this selection.", _body_muted_style)],
        onFirstPage=decorate, onLaterPages=decorate, canvasmaker=_NumberedCanvas,
    )
    return buf.getvalue()
