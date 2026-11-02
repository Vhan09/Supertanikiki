import streamlit as st

from config import APP_NAME, APP_ICON
from modules.dashboard.dashboard import render_dashboard
from utils.session import initialize_session

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_session()

st.sidebar.title(f"{APP_ICON} {APP_NAME}")
st.sidebar.caption("Basic Edition · Daily Business Management")

menu = st.sidebar.radio(
    "Navigasi",
    [
        "Dashboard",
        "Inventaris & Gudang",
        "Penjualan & Distribusi",
        "Pembelian & Supplier",
        "Keuangan & Akuntansi",
        "Wilayah / Rayon",
        "Laporan & Dokumen",
    ],
)

if menu == "Dashboard":
    render_dashboard()
else:
    st.title(menu)
    st.info(
        "Modul ini sudah disiapkan dalam struktur aplikasi dan akan kita bangun "
        "bertahap. Untuk saat ini belum ada transaksi permanen."
    )
    st.caption("Data sementara disimpan dalam sesi aplikasi (session state).")
