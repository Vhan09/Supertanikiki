"""Create Excel reports with the shared Supertani Indonesia report styling."""
from __future__ import annotations

from datetime import date
from io import BytesIO

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.properties import PageSetupProperties

NAVY = "1F3864"
BLUE = "0F3D63"
GOLD = "FFF200"
PALE = "EEF2F8"
MUTED = "536575"


def _prepare_workbook(xlsx_bytes: bytes, title: str) -> bytes:
    workbook = load_workbook(BytesIO(xlsx_bytes))
    workbook.properties.title = title
    workbook.properties.creator = "Supertani Indonesia"
    for worksheet in workbook.worksheets:
        if worksheet.sheet_properties.pageSetUpPr is None:
            worksheet.sheet_properties.pageSetUpPr = PageSetupProperties()
        worksheet.sheet_properties.pageSetUpPr.fitToPage = True
        worksheet.page_setup.orientation = worksheet.page_setup.orientation or "landscape"
        worksheet.page_setup.paperSize = worksheet.page_setup.paperSize or worksheet.PAPERSIZE_A4
        worksheet.page_setup.fitToWidth = worksheet.page_setup.fitToWidth or 1
        if worksheet.page_setup.fitToHeight is None:
            worksheet.page_setup.fitToHeight = 0
        worksheet.page_margins.left = worksheet.page_margins.right = 0.4
        worksheet.page_margins.top = worksheet.page_margins.bottom = 0.55
        worksheet.page_margins.header = 0.2
        worksheet.page_margins.footer = 0.25
        worksheet.oddFooter.left.text = f"Supertani Indonesia | {title}"
        worksheet.oddFooter.left.size = 8
        worksheet.oddFooter.left.font = "Arial"
        worksheet.oddFooter.left.color = MUTED
        worksheet.oddFooter.right.text = "Dicetak &D | Halaman &P dari &N"
        worksheet.oddFooter.right.size = 8
        worksheet.oddFooter.right.font = "Arial"
        worksheet.oddFooter.right.color = MUTED
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def export_dataframe(frame: pd.DataFrame, sheet_name: str, title: str) -> bytes:
    """Create a formatted XLSX report from a dataframe."""
    if len(frame.columns) == 0:
        raise ValueError("Excel report must contain at least one column.")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name=sheet_name, index=False, startrow=3)
        worksheet = writer.book[sheet_name]
        last_column = len(frame.columns)
        last_letter = worksheet.cell(row=1, column=last_column).column_letter
        worksheet.sheet_view.showGridLines = False
        worksheet.freeze_panes = "A5"
        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_column)
        worksheet["A1"] = title.upper()
        worksheet["A1"].font = Font(name="Arial", size=16, bold=True, color=NAVY)
        worksheet["A1"].alignment = Alignment(vertical="center")
        worksheet["A1"].fill = PatternFill("solid", fgColor=GOLD)
        worksheet.row_dimensions[1].height = 30
        worksheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_column)
        worksheet["A2"] = f"Tanggal cetak: {date.today():%d-%m-%Y}"
        worksheet["A2"].font = Font(name="Arial", size=9, color=MUTED)
        worksheet.row_dimensions[2].height = 20

        header_fill = PatternFill("solid", fgColor=BLUE)
        header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        accent_border = Border(bottom=Side(style="medium", color=GOLD))
        for cell in worksheet[4]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = accent_border
        worksheet.row_dimensions[4].height = 28

        for row_number in range(5, worksheet.max_row + 1):
            fill = PatternFill("solid", fgColor=PALE if row_number % 2 == 0 else "FFFFFF")
            for cell in worksheet[row_number]:
                cell.fill = fill
                cell.font = Font(name="Arial", size=10, color=NAVY)
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                cell.border = Border(bottom=Side(style="hair", color="D5E1EB"))
            worksheet.row_dimensions[row_number].height = 22

        for column_index, column in enumerate(worksheet.columns, start=1):
            column_letter = worksheet.cell(row=4, column=column_index).column_letter
            width = max(len(str(cell.value or "")) for cell in column) + 2
            worksheet.column_dimensions[column_letter].width = min(max(width, 12), 40)

        for cell in worksheet[4]:
            if cell.value in {"Stok Awal", "Masuk", "Keluar", "Stok Saat Ini", "Jumlah"}:
                for row in worksheet.iter_rows(
                    min_row=5, min_col=cell.column, max_col=cell.column
                ):
                    row[0].number_format = "#,##0.##"
            elif cell.value in {"Harga Beli", "Harga Jual", "Nilai Aset"}:
                for row in worksheet.iter_rows(
                    min_row=5, min_col=cell.column, max_col=cell.column
                ):
                    row[0].number_format = "#,##0"

        worksheet.auto_filter.ref = f"A4:{last_letter}{worksheet.max_row}"
        worksheet.print_title_rows = "1:4"
        worksheet.print_area = f"A1:{last_letter}{worksheet.max_row}"

    return _prepare_workbook(output.getvalue(), title)
