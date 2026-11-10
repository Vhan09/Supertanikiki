"""Create Kaizen PBG styled PDF reports and convert XLSX files to PDF."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from datetime import date, datetime
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Table,
    TableStyle,
)

from utils.excel_converter import _prepare_workbook

NAVY = colors.HexColor("#1F3864")
BLUE = colors.HexColor("#0F3D63")
GOLD = colors.HexColor("#FFF200")
PALE = colors.HexColor("#EEF2F8")
PALE_BLUE = colors.HexColor("#EAF3F9")
LINE = colors.HexColor("#8C96A3")
MUTED = colors.HexColor("#536575")
WHITE = colors.white


def _find_libreoffice() -> str | None:
    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if executable:
        return executable
    for candidate in (
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ):
        if os.path.exists(candidate):
            return candidate
    return None


def convert_xlsx_to_pdf(
    xlsx_bytes: bytes,
    title: str = "Laporan",
    *,
    fallback: Callable[[bytes], bytes | None] | None = None,
) -> bytes | None:
    """Convert XLSX bytes to PDF; use fallback bytes when LibreOffice is unavailable."""
    executable = _find_libreoffice()
    if not executable:
        return fallback(xlsx_bytes) if fallback else None

    prepared = _prepare_workbook(xlsx_bytes, title)
    with tempfile.TemporaryDirectory() as directory:
        source = os.path.join(directory, "laporan.xlsx")
        with open(source, "wb") as file:
            file.write(prepared)
        try:
            subprocess.run(
                [executable, "--headless", "--convert-to", "pdf", "--outdir", directory, source],
                check=True,
                timeout=120,
                capture_output=True,
            )
        except (subprocess.SubprocessError, OSError):
            return fallback(xlsx_bytes) if fallback else None
        output = os.path.join(directory, "laporan.pdf")
        if not os.path.exists(output):
            return fallback(xlsx_bytes) if fallback else None
        with open(output, "rb") as file:
            return file.read()


def save_excel_as_pdf(
    excel_path: str | Path,
    pdf_path: str | Path | None = None,
    *,
    title: str | None = None,
) -> Path:
    """Convert an XLSX file and save its PDF beside it (or at ``pdf_path``)."""
    source = Path(excel_path)
    destination = Path(pdf_path) if pdf_path else source.with_suffix(".pdf")
    report_title = title or source.stem.replace("_", " ")
    pdf_bytes = convert_xlsx_to_pdf(source.read_bytes(), report_title)
    if pdf_bytes is None:
        raise RuntimeError(
            "PDF conversion failed. Install LibreOffice or provide a working fallback."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(pdf_bytes)
    return destination


def safe_text(value: Any) -> str:
    """Escape plain text for ReportLab while supporting common math notation."""
    text = str(value).replace("φ", "phi")
    text = escape(text.encode("cp1252", "replace").decode("cp1252"))
    return (
        text.replace("²", "<super>2</super>")
        .replace("³", "<super>3</super>")
        .replace("\n", "<br/>")
    )


def paragraph(value: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(safe_text(value), style)


def styles(
    prefix: str = "kaizen",
    *,
    title_size: float = 14,
    body_size: float = 7,
    header_size: float | None = None,
) -> dict[str, ParagraphStyle]:
    header_size = header_size if header_size is not None else body_size
    return {
        "title": ParagraphStyle(
            f"{prefix}_title",
            fontName="Helvetica-Bold",
            fontSize=title_size,
            leading=title_size + 3,
            textColor=NAVY,
            spaceAfter=3,
        ),
        "subtitle": ParagraphStyle(
            f"{prefix}_subtitle",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=MUTED,
            spaceAfter=8,
        ),
        "section": ParagraphStyle(
            f"{prefix}_section",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "header": ParagraphStyle(
            f"{prefix}_header",
            fontName="Helvetica-Bold",
            fontSize=header_size,
            leading=header_size + 1.5,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "body": ParagraphStyle(
            f"{prefix}_body",
            fontName="Helvetica",
            fontSize=body_size,
            leading=body_size + 1.5,
        ),
        "body_center": ParagraphStyle(
            f"{prefix}_body_center",
            fontName="Helvetica",
            fontSize=body_size,
            leading=body_size + 1.5,
            alignment=TA_CENTER,
        ),
        "body_left": ParagraphStyle(
            f"{prefix}_body_left",
            fontName="Helvetica",
            fontSize=body_size,
            leading=body_size + 1.5,
            alignment=TA_LEFT,
        ),
        "label": ParagraphStyle(
            f"{prefix}_label",
            fontName="Helvetica-Bold",
            fontSize=max(6, body_size),
            leading=max(7.5, body_size + 1.5),
            textColor=NAVY,
        ),
        "small": ParagraphStyle(
            f"{prefix}_small",
            fontName="Helvetica",
            fontSize=max(6, body_size),
            leading=max(7.5, body_size + 1.5),
            textColor=MUTED,
        ),
    }


def document(
    buffer,
    title: str,
    *,
    pagesize=landscape(A4),
    margins_mm: tuple[float, float, float, float] = (12, 12, 12, 16),
) -> SimpleDocTemplate:
    """Create a report document. Margin order is left, right, top, bottom."""
    left, right, top, bottom = margins_mm
    return SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        leftMargin=left * mm,
        rightMargin=right * mm,
        topMargin=top * mm,
        bottomMargin=bottom * mm,
        title=title,
        author="Kaizen PBG",
    )


def table(
    rows: list[list[Any]],
    widths,
    header_style: ParagraphStyle,
    body_style: ParagraphStyle,
    *,
    centered: tuple[int, ...] = (),
    repeat_rows: int = 1,
    long: bool = True,
    row_backgrounds=None,
    extra_styles: list[tuple] | None = None,
):
    """Build a styled table; the first row is used as the repeating header."""
    if not rows:
        raise ValueError("Table must contain a header row.")
    centered_style = (
        ParagraphStyle(
            f"kaizen_table_center_{id(rows)}",
            parent=body_style,
            alignment=TA_CENTER,
        )
        if centered
        else body_style
    )
    cells = [[paragraph(value, header_style) for value in rows[0]]]
    for row in rows[1:]:
        cells.append(
            [
                paragraph(value, centered_style if index in centered else body_style)
                for index, value in enumerate(row)
            ]
        )
    table_type = LongTable if long else Table
    result = table_type(cells, colWidths=widths, repeatRows=repeat_rows, hAlign="LEFT")
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, GOLD),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), row_backgrounds or [WHITE, PALE]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if extra_styles:
        table_style.extend(extra_styles)
    result.setStyle(TableStyle(table_style))
    return result


def identity_table(rows: list[tuple[str, Any]], widths, label_style, body_style):
    """Build a compact label/value identity table."""
    if not rows:
        raise ValueError("Identity table must contain at least one row.")
    cells = [
        [paragraph(label, label_style), paragraph(value or "-", body_style)]
        for label, value in rows
    ]
    result = Table(cells, colWidths=widths, hAlign="LEFT")
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), PALE_BLUE),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return result


def footer(title: str):
    """Return a ReportLab page callback with title, print time, and page number."""
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D5E1EB"))
        canvas.line(doc.leftMargin, 10 * mm, doc.pagesize[0] - doc.rightMargin, 10 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#65727D"))
        canvas.drawString(doc.leftMargin, 6 * mm, f"Kaizen PBG - {title}")
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            6 * mm,
            f"Dicetak {datetime.now():%d-%m-%Y %H:%M} | Halaman {doc.page}",
        )
        canvas.restoreState()

    return draw


def render_pdf(title: str, story: list[Any]) -> bytes:
    """Render a report using the shared page layout and footer."""
    output = BytesIO()
    doc = document(output, title)
    page_footer = footer(title)
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return output.getvalue()


def build_pdf(
    output_path: str | Path,
    title: str,
    story: list[Any],
    *,
    pagesize=landscape(A4),
    margins_mm: tuple[float, float, float, float] = (12, 12, 12, 16),
) -> Path:
    """Write a PDF report with the shared layout and footer."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    doc = document(
        str(destination),
        title,
        pagesize=pagesize,
        margins_mm=margins_mm,
    )
    page_footer = footer(title)
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return destination


def inventory_pdf(items: list[dict]) -> bytes:
    title = "LAPORAN INVENTARIS SUPERTANI"
    report_styles = styles(prefix="inventory")
    story = [
        paragraph(title, report_styles["title"]),
        paragraph(f"Tanggal cetak: {date.today():%d-%m-%Y}", report_styles["subtitle"]),
    ]
    rows = [["Kode", "Nama Produk", "Kategori", "Stok", "Satuan", "Nilai Aset"]]
    for item in items:
        asset = float(item["stok"]) * float(item["harga_beli"])
        rows.append(
            [
                item["kode_produk"],
                item["nama_produk"],
                item["kategori"],
                f'{float(item["stok"]):g}',
                item["satuan"],
                f"Rp {asset:,.0f}",
            ]
        )
    story.append(
        table(
            rows,
            [30 * mm, 70 * mm, 42 * mm, 30 * mm, 28 * mm, 73 * mm],
            report_styles["header"],
            report_styles["body"],
            centered=(0, 3, 4),
        )
    )
    return render_pdf(title, story)


def movements_pdf(items: list[dict]) -> bytes:
    title = "RIWAYAT PERGERAKAN STOK SUPERTANI"
    report_styles = styles(prefix="movements", body_size=6, header_size=6)
    story = [
        paragraph(title, report_styles["title"]),
        paragraph(f"Tanggal cetak: {date.today():%d-%m-%Y}", report_styles["subtitle"]),
    ]
    rows = [["ID", "Tanggal", "Kode", "Jenis", "Jumlah", "Gudang", "Referensi", "Keterangan"]]
    for item in items:
        rows.append(
            [
                item["id"],
                item["tanggal"],
                item["kode_produk"],
                item["jenis"],
                f'{float(item["jumlah"]):g}',
                item["gudang"] or "",
                item["referensi"] or "",
                item["keterangan"] or "",
            ]
        )
    story.append(
        table(
            rows,
            [10 * mm, 25 * mm, 30 * mm, 23 * mm, 20 * mm, 35 * mm, 30 * mm, 85 * mm],
            report_styles["header"],
            report_styles["body"],
            centered=(0, 1, 3, 4),
        )
    )
    return render_pdf(title, story)


def _main() -> None:
    parser = argparse.ArgumentParser(description="Convert an XLSX workbook to a styled PDF.")
    parser.add_argument("excel_file", type=Path, help="Input .xlsx file")
    parser.add_argument("pdf_file", type=Path, nargs="?", help="Output .pdf file")
    parser.add_argument("--title", help="Report title shown in PDF metadata and footer")
    args = parser.parse_args()
    output = save_excel_as_pdf(args.excel_file, args.pdf_file, title=args.title)
    print(f"PDF saved: {output}")


if __name__ == "__main__":
    _main()
