"""Distributor sales and distribution register."""
from __future__ import annotations

from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st
from reportlab.lib.enums import TA_CENTER
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.properties import PageSetupProperties
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, TableStyle

from services.sales_service import (
    add_distributor_order,
    delete_distributor_order,
    list_distributor_orders,
)
from utils.excel_converter import _prepare_workbook
from utils.pdf_converter import document, footer, paragraph, styles


REPORT_TITLE = "REKAP DISTRIBUTOR PUPUK ORGANIK SUPERTANI DI WILAYAH"
REPORT_COLUMNS = [
    "Nomor Surat",
    "Nama Perusahaan",
    "NPWP",
    "No. Rekening",
    "Alamat",
    "Kab/Prov",
    "Box",
    "Karton",
]
EXCEL_WIDTHS = [6, 20, 30, 19, 22, 38, 21, 12, 12]
PDF_WIDTHS_MM = [9, 29, 42, 28, 33, 54, 35, 22, 22]


def _report_records(
    orders: list[dict],
    minimum_rows: int = 21,
) -> list[list[object]]:
    records = [
        [
            index,
            order.get("nomor_surat", ""),
            order.get("nama_perusahaan", ""),
            order.get("npwp", ""),
            order.get("no_rekening", ""),
            order.get("alamat", ""),
            order.get("kab_prov", ""),
            order.get("box", 0),
            order.get("karton", 0),
        ]
        for index, order in enumerate(orders, start=1)
    ]
    for index in range(len(records) + 1, minimum_rows + 1):
        records.append([index, "", "", "", "", "", "", "", ""])
    return records


def distributor_excel(orders: list[dict], wilayah: str = "SEMUA WILAYAH") -> bytes:
    """Build a formatted, landscape Excel report with grouped table headers."""
    workbook_stream = BytesIO()
    from openpyxl import Workbook

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Rekap Distributor"
    worksheet.sheet_view.showGridLines = False

    worksheet.merge_cells("A1:I1")
    worksheet["A1"] = f"{REPORT_TITLE} {wilayah.upper()}"
    worksheet["A1"].font = Font(name="Arial", size=15, bold=True, color="1F3864")
    worksheet["A1"].alignment = Alignment(horizontal="center", vertical="center")
    worksheet["A1"].fill = PatternFill("solid", fgColor="FFF200")
    worksheet.row_dimensions[1].height = 30

    worksheet.merge_cells("A2:I2")
    worksheet["A2"] = f"Tanggal cetak: {date.today():%d-%m-%Y}"
    worksheet["A2"].font = Font(name="Arial", size=9, color="536575")
    worksheet["A2"].alignment = Alignment(vertical="center")
    worksheet.row_dimensions[2].height = 20

    headers = [
        ("A4:A5", "NO"),
        ("B4:B5", "Nomor Surat"),
        ("C4:C5", "Nama Perusahaan"),
        ("D4:D5", "NPWP"),
        ("E4:E5", "No. Rekening"),
        ("F4:G4", "Pengiriman"),
        ("H4:I4", "Banyak Orderan"),
    ]
    for cell_range, label in headers:
        worksheet.merge_cells(cell_range)
        cell = worksheet[cell_range.split(":")[0]]
        cell.value = label
    worksheet["F5"] = "Alamat"
    worksheet["G5"] = "Kab/Prov"
    worksheet["H5"] = "Box"
    worksheet["I5"] = "Karton"

    header_fill = PatternFill("solid", fgColor="0F3D63")
    header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin", color="667085"),
        right=Side(style="thin", color="667085"),
        top=Side(style="thin", color="667085"),
        bottom=Side(style="thin", color="667085"),
    )
    for row in worksheet.iter_rows(min_row=4, max_row=5, min_col=1, max_col=9):
        for cell in row:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
    worksheet.row_dimensions[4].height = 24
    worksheet.row_dimensions[5].height = 22

    for row_number, record in enumerate(_report_records(orders), start=6):
        for column_number, value in enumerate(record, start=1):
            cell = worksheet.cell(row=row_number, column=column_number, value=value)
            if isinstance(value, str):
                cell.data_type = "s"
                cell.number_format = "@"
            cell.font = Font(name="Arial", size=9, color="1F3864")
            cell.alignment = Alignment(
                horizontal="center" if column_number in (1, 8, 9) else "left",
                vertical="center",
                wrap_text=True,
            )
            cell.fill = PatternFill("solid", fgColor="EEF2F8" if row_number % 2 == 0 else "FFFFFF")
            cell.border = thin_border
        worksheet.row_dimensions[row_number].height = 28

    for index, width in enumerate(EXCEL_WIDTHS, start=1):
        worksheet.column_dimensions[get_column_letter(index)].width = width
    last_row = max(6, worksheet.max_row)
    worksheet.freeze_panes = "A6"
    worksheet.print_title_rows = "1:5"
    worksheet.print_area = f"A1:I{last_row}"
    worksheet.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True, autoPageBreaks=False)
    worksheet.page_setup.orientation = "landscape"
    worksheet.page_setup.paperSize = worksheet.PAPERSIZE_A4
    worksheet.page_setup.fitToWidth = 1
    worksheet.page_setup.fitToHeight = 0
    worksheet.page_margins.left = worksheet.page_margins.right = 0.25
    worksheet.page_margins.top = worksheet.page_margins.bottom = 0.5
    worksheet.oddFooter.left.text = "Supertani Indonesia | Rekap distributor"
    worksheet.oddFooter.right.text = "Dicetak &D | Halaman &P dari &N"
    workbook.save(workbook_stream)
    return _prepare_workbook(workbook_stream.getvalue(), REPORT_TITLE)


def distributor_pdf(orders: list[dict], wilayah: str = "SEMUA WILAYAH") -> bytes:
    """Build the matching landscape PDF report."""
    pdf_styles = styles(prefix="distributor", title_size=12, body_size=6.5, header_size=7)
    pdf_styles["title"].alignment = TA_CENTER
    story = [
        paragraph(f"{REPORT_TITLE} {wilayah.upper()}", pdf_styles["title"]),
        paragraph(f"Tanggal cetak: {date.today():%d-%m-%Y}", pdf_styles["subtitle"]),
    ]
    header_style = pdf_styles["header"]
    body_style = pdf_styles["body"]
    center_style = pdf_styles["body_center"]
    rows = [
        [
            paragraph("NO", header_style),
            paragraph("Nomor Surat", header_style),
            paragraph("Nama Perusahaan", header_style),
            paragraph("NPWP", header_style),
            paragraph("No. Rekening", header_style),
            paragraph("Pengiriman", header_style),
            "",
            paragraph("Banyak Orderan", header_style),
            "",
        ],
        ["", "", "", "", "", paragraph("Alamat", header_style),
         paragraph("Kab/Prov", header_style), paragraph("Box", header_style),
         paragraph("Karton", header_style)],
    ]
    for record in _report_records(orders):
        rows.append(
            [
                paragraph(value, center_style if index in (0, 7, 8) else body_style)
                for index, value in enumerate(record)
            ]
        )

    report_table = LongTable(
        rows,
        colWidths=[width * mm for width in PDF_WIDTHS_MM],
        repeatRows=2,
        hAlign="LEFT",
    )
    report_table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (0, 1)),
                ("SPAN", (1, 0), (1, 1)),
                ("SPAN", (2, 0), (2, 1)),
                ("SPAN", (3, 0), (3, 1)),
                ("SPAN", (4, 0), (4, 1)),
                ("SPAN", (5, 0), (6, 0)),
                ("SPAN", (7, 0), (8, 0)),
                ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#0F3D63")),
                ("TEXTCOLOR", (0, 0), (-1, 1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#667085")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 1), "CENTER"),
                ("ALIGN", (0, 2), (0, -1), "CENTER"),
                ("ALIGN", (7, 2), (8, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 2), (-1, -1), [colors.white, colors.HexColor("#EEF2F8")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(report_table)

    output = BytesIO()
    doc = document(output, REPORT_TITLE, pagesize=landscape(A4), margins_mm=(8, 8, 12, 16))
    page_footer = footer(REPORT_TITLE)
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return output.getvalue()


def render_sales() -> None:
    st.title("Penjualan & Distribusi")
    st.caption("Rekap distributor pupuk organik dengan ekspor Excel dan PDF siap cetak landscape.")

    with st.expander("Tambah data distributor", expanded=True):
        with st.form("distributor_order_form", clear_on_submit=True):
            first, second = st.columns(2)
            nomor_surat = first.text_input("Nomor surat")
            nama_perusahaan = second.text_input("Nama perusahaan *")
            npwp = first.text_input("NPWP")
            no_rekening = second.text_input("No. rekening")
            alamat = st.text_input("Alamat pengiriman")
            kab_prov = st.text_input("Kabupaten / Provinsi")
            quantity_box, quantity_carton = st.columns(2)
            box = quantity_box.number_input("Banyak orderan (Box)", min_value=0, step=1)
            karton = quantity_carton.number_input("Banyak orderan (Karton)", min_value=0, step=1)
            submitted = st.form_submit_button("Simpan distributor", type="primary")
            if submitted:
                if not nama_perusahaan.strip():
                    st.error("Nama perusahaan wajib diisi.")
                else:
                    add_distributor_order(
                        {
                            "nomor_surat": nomor_surat,
                            "nama_perusahaan": nama_perusahaan,
                            "npwp": npwp,
                            "no_rekening": no_rekening,
                            "alamat": alamat,
                            "kab_prov": kab_prov,
                            "box": box,
                            "karton": karton,
                        }
                    )
                    st.success("Data distributor berhasil disimpan.")
                    st.rerun()

    orders = list_distributor_orders()
    locations = sorted({str(order["kab_prov"]).strip() for order in orders if order["kab_prov"]})
    selected_wilayah = st.selectbox("Filter wilayah", ["Semua wilayah", *locations])
    filtered = (
        orders
        if selected_wilayah == "Semua wilayah"
        else [order for order in orders if order["kab_prov"] == selected_wilayah]
    )
    title_wilayah = selected_wilayah.upper()

    st.subheader(f"{REPORT_TITLE} {title_wilayah}")
    if not filtered:
        st.info("Belum ada data distributor untuk wilayah ini. Tambahkan data melalui formulir di atas.")
    display_rows = _report_records(filtered)
    frame = pd.DataFrame(display_rows, columns=["NO", *REPORT_COLUMNS])
    st.dataframe(
        frame,
        hide_index=True,
        column_config={
            "NO": st.column_config.NumberColumn("NO", width="small"),
            "Box": st.column_config.NumberColumn("Box", width="small"),
            "Karton": st.column_config.NumberColumn("Karton", width="small"),
        },
    )

    download_col, delete_col = st.columns(2)
    file_date = date.today().isoformat()
    download_col.download_button(
        "Unduh Excel",
        data=distributor_excel(filtered, title_wilayah),
        file_name=f"rekap_distributor_{file_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    download_col.download_button(
        "Unduh PDF landscape",
        data=distributor_pdf(filtered, title_wilayah),
        file_name=f"rekap_distributor_{file_date}.pdf",
        mime="application/pdf",
    )

    if orders:
        with delete_col:
            selected_order = st.selectbox(
                "Hapus data distributor",
                options=orders,
                format_func=lambda order: f'{order["nama_perusahaan"]} · {order["kab_prov"] or "Wilayah belum diisi"}',
                key="sales_delete_order",
            )
            if st.button("Hapus data terpilih"):
                delete_distributor_order(selected_order["id"])
                st.success("Data distributor berhasil dihapus.")
                st.rerun()
