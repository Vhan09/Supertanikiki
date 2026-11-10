from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table as ExcelTable, TableStyleInfo

from services.inventory_service import (
    add_movement,
    delete_movement,
    get_inventory,
    import_movements,
    initialize_inventory_db,
    list_movements,
    replace_products,
    seed_sample_products,
    upsert_products,
)
from utils.excel_converter import export_dataframe
from utils.pdf_converter import inventory_pdf, movements_pdf


def normalize_column_names(frame: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "kode": "kode_produk",
        "kode barang": "kode_produk",
        "kode_barang": "kode_produk",
        "nama": "nama_produk",
        "nama barang": "nama_produk",
        "nama_barang": "nama_produk",
        "stock awal": "stok_awal",
        "stock_awal": "stok_awal",
        "stok": "stok_awal",
        "harga jual": "harga_satuan",
        "harga_jual_satuan": "harga_satuan",
        "harga_jual": "harga_satuan",
        "tipe": "jenis",
        "qty": "jumlah",
    }
    normalized = {}
    for column in frame.columns:
        key = str(column).strip().lower().replace("-", "_").replace(" ", "_")
        key = aliases.get(key, key)
        normalized[column] = key
    return frame.rename(columns=normalized)


def normalize_products(frame: pd.DataFrame) -> pd.DataFrame:
    frame = normalize_column_names(frame)
    required = {"kode_produk", "nama_produk"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Kolom wajib Products: kode_produk dan nama_produk")
    frame = frame.where(pd.notna(frame), "")
    frame["kode_produk"] = frame["kode_produk"].astype(str).str.strip()
    frame["nama_produk"] = frame["nama_produk"].astype(str).str.strip()
    frame["kategori"] = frame.get("kategori", "")
    frame["satuan"] = frame.get("satuan", "")
    frame["stok_awal"] = pd.to_numeric(frame.get("stok_awal", 0), errors="coerce").fillna(0)
    frame["harga_beli"] = pd.to_numeric(frame.get("harga_beli", 0), errors="coerce").fillna(0)
    frame["harga_satuan"] = pd.to_numeric(frame.get("harga_satuan", 0), errors="coerce").fillna(0)
    return frame


def normalize_movements(frame: pd.DataFrame) -> pd.DataFrame:
    frame = normalize_column_names(frame)
    required = {"tanggal", "kode_produk", "jenis", "jumlah"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Kolom wajib Stock_Movement: tanggal, kode_produk, jenis, jumlah")
    frame = frame.where(pd.notna(frame), "")
    frame["tanggal"] = pd.to_datetime(frame["tanggal"], errors="coerce")
    frame["tanggal"] = frame["tanggal"].dt.strftime("%Y-%m-%d")
    frame["kode_produk"] = frame["kode_produk"].astype(str).str.strip()
    frame["jenis"] = frame["jenis"].astype(str).str.strip().str.upper()
    frame["jumlah"] = pd.to_numeric(frame["jumlah"], errors="coerce")
    return frame


def excel_template() -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        products = pd.DataFrame([{
            "kode_produk": "PRD-CONTOH", "nama_produk": "Pupuk Contoh",
            "kategori": "NPK", "satuan": "Sak (50kg)", "stok_awal": 100,
            "harga_beli": 100000, "harga_jual": 125000
        }])
        movements = pd.DataFrame([{
            "tanggal": "2026-11-02", "kode_produk": "PRD-CONTOH", "jenis": "MASUK",
            "jumlah": 10, "gudang": "Gudang Utama", "referensi": "PO-001",
            "keterangan": "Contoh barang masuk"
        }])
        products.to_excel(writer, sheet_name="Products", index=False, startrow=3)
        movements.to_excel(writer, sheet_name="Stock_Movement", index=False, startrow=3)

        thin_green = Side(style="thin", color="8DA399")
        for sheet_name, title, subtitle, frame in [
            ("Products", "MASTER DATA PRODUK", "Isi satu produk per baris. Kolom kode_produk dan nama_produk wajib diisi.", products),
            ("Stock_Movement", "FORMULIR PERGERAKAN STOK", "Isi transaksi barang masuk atau keluar. Kolom kode_produk harus sama dengan sheet Products.", movements),
        ]:
            sheet = writer.book[sheet_name]
            sheet.sheet_view.showGridLines = False
            sheet.freeze_panes = "A5"
            sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(frame.columns))
            sheet["A1"] = title
            sheet["A1"].font = Font(size=18, bold=True, color="173D32")
            sheet["A1"].alignment = Alignment(vertical="center")
            sheet.row_dimensions[1].height = 32
            sheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(frame.columns))
            sheet["A2"] = subtitle
            sheet["A2"].font = Font(size=10, italic=True, color="4F645C")
            sheet["A2"].alignment = Alignment(wrap_text=True, vertical="center")
            sheet.row_dimensions[2].height = 28
            header_row = 4
            for cell in sheet[header_row]:
                if cell.column <= len(frame.columns):
                    cell.fill = PatternFill("solid", fgColor="173D32")
                    cell.font = Font(color="FFFFFF", bold=True)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    cell.border = Border(bottom=thin_green)
            sheet.row_dimensions[header_row].height = 28
            for row in sheet.iter_rows(min_row=5, max_row=24, min_col=1, max_col=len(frame.columns)):
                for cell in row:
                    cell.border = Border(bottom=Side(style="hair", color="D9E2DE"))
                    cell.alignment = Alignment(vertical="center")
            widths = {
                "Products": [18, 34, 18, 18, 14, 16, 16],
                "Stock_Movement": [16, 18, 18, 16, 12, 22, 18, 34],
            }
            for index, width in enumerate(widths[sheet_name], start=1):
                sheet.column_dimensions[chr(64 + index)].width = width
            sheet.auto_filter.ref = f"A4:{chr(64 + len(frame.columns))}24"
            sheet.page_setup.orientation = "landscape"
            sheet.page_setup.fitToWidth = 1
            sheet.page_setup.fitToHeight = 0
            sheet.sheet_properties.pageSetUpPr.fitToPage = True
            sheet.print_title_rows = "1:4"
            sheet.print_area = f"A1:{chr(64 + len(frame.columns))}24"
            sheet.page_margins.left = 0.25
            sheet.page_margins.right = 0.25
            sheet.page_margins.top = 0.4
            sheet.page_margins.bottom = 0.4
            table = ExcelTable(1, f"{sheet_name.replace('_', '')}Table",
                          f"A4:{chr(64 + len(frame.columns))}5")
            table.tableStyleInfo = TableStyleInfo(
                name="TableStyleMedium4", showFirstColumn=False,
                showLastColumn=False, showRowStripes=True, showColumnStripes=False
            )
            sheet.add_table(table)
            sheet["F5"].number_format = '#,##0'
            sheet["G5"].number_format = '#,##0'

        movement_sheet = writer.book["Stock_Movement"]
        kind_validation = DataValidation(type="list", formula1='"MASUK,KELUAR"', allow_blank=False)
        movement_sheet.add_data_validation(kind_validation)
        kind_validation.add("D5:D500")

        instruction = writer.book.create_sheet("Petunjuk", 0)
        instruction.sheet_view.showGridLines = False
        instruction.column_dimensions["A"].width = 24
        instruction.column_dimensions["B"].width = 72
        instructions = [
            ("Products", "kode_produk, nama_produk wajib diisi. Gunakan kode produk yang sama pada kedua sheet."),
            ("Stock_Movement", "tanggal memakai format YYYY-MM-DD. jenis hanya MASUK atau KELUAR."),
            ("Peringatan", "Jangan mengubah nama sheet dan nama header."),
        ]
        instruction.merge_cells("A1:B1")
        instruction["A1"] = "PETUNJUK TEMPLATE INVENTARIS SUPERTANI"
        instruction["A1"].font = Font(size=18, bold=True, color="FFFFFF")
        instruction["A1"].fill = PatternFill("solid", fgColor="173D32")
        instruction["A1"].alignment = Alignment(horizontal="center", vertical="center")
        instruction.row_dimensions[1].height = 34
        instruction["A2"] = "LANGKAH PENGISIAN"
        instruction["B2"] = "Isi data secara berurutan pada sheet Products dan Stock_Movement."
        instruction["A2"].font = instruction["B2"].font = Font(bold=True, color="173D32")
        for row, (label, text) in enumerate(instructions, start=3):
            instruction.cell(row, 1, label)
            instruction.cell(row, 2, text)
            instruction.cell(row, 1).font = Font(bold=True, color="173D32")
            instruction.cell(row, 1).fill = PatternFill("solid", fgColor="EAF2EE")
            instruction.cell(row, 1).border = instruction.cell(row, 2).border = Border(bottom=thin_green)
            instruction.row_dimensions[row].height = 28
            instruction.cell(row, 2).alignment = Alignment(wrap_text=True, vertical="center")
        instruction.page_setup.orientation = "portrait"
        instruction.page_setup.fitToWidth = 1
        instruction.sheet_properties.pageSetUpPr.fitToPage = True
    return output.getvalue()


def inventory_excel(items: list[dict]) -> bytes:
    frame = pd.DataFrame(items)
    columns = {
        "kode_produk": "Kode",
        "nama_produk": "Nama Produk",
        "kategori": "Kategori",
        "stok_awal": "Stok Awal",
        "barang_masuk": "Masuk",
        "barang_keluar": "Keluar",
        "stok": "Stok Saat Ini",
        "satuan": "Satuan",
        "harga_beli": "Harga Beli",
        "harga_satuan": "Harga Jual",
    }
    frame = frame[list(columns)].rename(columns=columns)
    return export_dataframe(frame, "Ringkasan Stok", "Laporan Inventaris SuperTani")


def movements_excel(items: list[dict]) -> bytes:
    frame = pd.DataFrame(items)[[
        "id", "tanggal", "kode_produk", "jenis", "jumlah",
        "gudang", "referensi", "keterangan"
    ]]
    return export_dataframe(frame, "Stock_Movement", "Riwayat Pergerakan Stok SuperTani")


def movement_period(frame: pd.DataFrame, period: str) -> pd.DataFrame:
    frame = frame.copy()
    frame["Tanggal"] = pd.to_datetime(frame["Tanggal"], errors="coerce")
    frame = frame.dropna(subset=["Tanggal"])
    if period == "Mingguan":
        frame["Periode"] = frame["Tanggal"] - pd.to_timedelta(frame["Tanggal"].dt.dayofweek, unit="D")
        frame["Periode"] = frame["Periode"].dt.strftime("%d-%m-%Y")
    else:
        frame["Periode"] = frame["Tanggal"].dt.strftime("%m-%Y")
    summary = frame.groupby(["Periode", "Jenis"], dropna=False)["Jumlah"].sum().unstack(fill_value=0).reset_index()
    for kind in ["MASUK", "KELUAR"]:
        if kind not in summary.columns:
            summary[kind] = 0
    summary["Saldo Perubahan"] = summary["MASUK"] - summary["KELUAR"]
    return summary[["Periode", "MASUK", "KELUAR", "Saldo Perubahan"]].sort_values("Periode")


def render_inventaris_page() -> None:
    initialize_inventory_db()
    seed_sample_products()

    st.title("Inventaris & Gudang")
    st.caption("Kelola produk, stok awal, barang masuk, barang keluar, dan laporan PDF.")

    tabs = st.tabs(["Ringkasan Stok", "Import Excel", "Transaksi", "Riwayat"])
    inventory = get_inventory()

    with tabs[0]:
        if inventory:
            values = pd.DataFrame(inventory)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Jenis Produk", len(values))
            c2.metric("Total Stok", f"{values['stok'].sum():g}")
            c3.metric("Stok Menipis", int((values['stok'] < 20).sum()))
            c4.metric("Nilai Aset", f"Rp {sum(values['stok'] * values['harga_beli']):,.0f}")

            search = st.text_input("Cari produk", placeholder="Kode atau nama produk")
            filtered = values.copy()
            if search:
                filtered = filtered[
                    filtered["kode_produk"].str.contains(search, case=False, na=False)
                    | filtered["nama_produk"].str.contains(search, case=False, na=False)
                ]

            display = filtered[["kode_produk", "nama_produk", "kategori", "satuan", "stok_awal", "barang_masuk", "barang_keluar", "stok", "harga_beli", "harga_satuan"]].rename(columns={
                "kode_produk": "Kode", "nama_produk": "Nama Produk", "kategori": "Kategori", "satuan": "Satuan",
                "stok_awal": "Stok Awal", "barang_masuk": "Masuk", "barang_keluar": "Keluar", "stok": "Stok Saat Ini",
                "harga_beli": "Harga Beli", "harga_satuan": "Harga Jual"
            })
            st.dataframe(display, use_container_width=True, hide_index=True)
            download_cols = st.columns(2)
            download_cols[0].download_button("Unduh Excel", data=inventory_excel(filtered.to_dict("records")),
                                             file_name=f"laporan_inventaris_{date.today()}.xlsx",
                                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                             use_container_width=True)
            download_cols[1].download_button("Cetak / Unduh PDF", data=inventory_pdf(filtered.to_dict("records")),
                                             file_name=f"laporan_inventaris_{date.today()}.pdf",
                                             mime="application/pdf", use_container_width=True)
        else:
            st.info("Belum ada produk. Unduh template Excel pada tab Import Excel, lalu unggah database barang.")

    with tabs[1]:
        st.subheader("Import database Excel")
        st.download_button("Unduh template Excel", data=excel_template(),
                           file_name="template_inventaris_supertani.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        uploaded = st.file_uploader("Unggah file Excel", type=["xlsx"])
        replace = st.checkbox("Ganti data produk lama dengan data Excel", value=False)

        if uploaded and st.button("Proses file Excel", type="primary"):
            try:
                # Membaca satu kali dari buffer menghindari pointer UploadFile
                # berpindah setelah sheet pertama diproses.
                excel_buffer = BytesIO(uploaded.getvalue())
                excel = pd.ExcelFile(excel_buffer)
                st.info(f"Sheet ditemukan: {', '.join(excel.sheet_names)}")

                processed = False
                sheet_lookup = {
                    name.lower().replace(" ", "_").replace("-", "_"): name
                    for name in excel.sheet_names
                }
                if "products" in sheet_lookup:
                    excel_buffer.seek(0)
                    products = normalize_products(pd.read_excel(excel_buffer, sheet_name=sheet_lookup["products"]))
                    if replace:
                        count = replace_products(products.to_dict("records"))
                        st.success(f"Database produk diganti dengan {count} produk.")
                    else:
                        added, updated = upsert_products(products.to_dict("records"))
                        st.success(f"Produk diproses: {added} ditambahkan, {updated} diperbarui.")
                    processed = True

                if "stock_movement" in sheet_lookup or "stock movement" in sheet_lookup:
                    excel_buffer.seek(0)
                    movement_sheet = sheet_lookup.get("stock_movement") or sheet_lookup["stock movement"]
                    movements = normalize_movements(pd.read_excel(excel_buffer, sheet_name=movement_sheet))
                    imported, errors = import_movements(movements.to_dict("records"))
                    st.success(f"Transaksi diproses: {imported} berhasil.")
                    if errors:
                        st.warning("Beberapa baris dilewati: " + "; ".join(errors[:5]))
                    processed = True

                if not processed:
                    st.warning("File tidak memiliki sheet Products atau Stock_Movement.")
                else:
                    st.success("Import Excel selesai. Refresh halaman untuk melihat stok terbaru.")
                    st.rerun()
            except Exception as exc:
                st.error(f"Import gagal: {exc}")

    with tabs[2]:
        st.subheader("Catat barang masuk atau keluar")
        products = get_inventory()
        product_codes = [f"{item['kode_produk']} - {item['nama_produk']}" for item in products]
        if not product_codes:
            st.info("Tidak ada produk tersedia.")
        else:
            with st.form("stock_movement_form", clear_on_submit=True):
                selected = st.selectbox("Produk", product_codes)
                kode_produk = selected.split(" - ", 1)[0]
                c1, c2, c3 = st.columns(3)
                tanggal = c1.date_input("Tanggal", value=date.today())
                jenis = c2.selectbox("Jenis", ["MASUK", "KELUAR"])
                jumlah = c3.number_input("Jumlah", min_value=1.0, value=1.0, step=1.0)
                c1, c2 = st.columns(2)
                gudang = c1.text_input("Gudang", value="Gudang Utama")
                referensi = c2.text_input("Referensi", placeholder="PO-001 / SO-001")
                keterangan = st.text_input("Keterangan")
                if st.form_submit_button("Simpan transaksi", use_container_width=True):
                    try:
                        add_movement({
                            "tanggal": tanggal.isoformat(), "kode_produk": kode_produk,
                            "jenis": jenis, "jumlah": jumlah, "gudang": gudang,
                            "referensi": referensi, "keterangan": keterangan,
                        })
                        st.success("Transaksi stok berhasil disimpan.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    with tabs[3]:
        st.subheader("Riwayat pergerakan stok")
        movements = list_movements()
        if movements:
            frame = pd.DataFrame(movement for movement in movements)[[
                "id", "tanggal", "kode_produk", "jenis", "jumlah", "gudang", "referensi", "keterangan"
            ]].rename(columns={
                "id": "ID", "tanggal": "Tanggal", "kode_produk": "Kode", "jenis": "Jenis",
                "jumlah": "Jumlah", "gudang": "Gudang", "referensi": "Referensi", "keterangan": "Keterangan"
            })
            st.dataframe(frame, use_container_width=True, hide_index=True)
            st.divider()
            st.subheader("Ringkasan perubahan periode")
            period = st.radio("Periode", ["Mingguan", "Bulanan"], horizontal=True)
            history = movement_period(frame, period)
            history_display = history.rename(columns={
                "MASUK": "Barang Masuk",
                "KELUAR": "Barang Keluar",
                "Saldo Perubahan": "Saldo Perubahan",
            })
            st.dataframe(history_display, use_container_width=True, hide_index=True)
            export_cols = st.columns(2)
            export_cols[0].download_button("Unduh Excel", data=movements_excel(movements),
                                           file_name=f"riwayat_stok_{date.today()}.xlsx",
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           use_container_width=True)
            export_cols[1].download_button("Unduh PDF", data=movements_pdf(movements),
                                           file_name=f"riwayat_stok_{date.today()}.pdf",
                                           mime="application/pdf", use_container_width=True)
            delete_id = st.number_input("ID transaksi yang akan dihapus", min_value=1, step=1, value=1)
            if st.button("Hapus transaksi"):
                delete_movement(int(delete_id))
                st.success("Transaksi dihapus dan stok dihitung ulang.")
                st.rerun()
        else:
            st.info("Belum ada riwayat barang masuk atau keluar.")


if __name__ == "__main__":
    render_inventaris_page()
