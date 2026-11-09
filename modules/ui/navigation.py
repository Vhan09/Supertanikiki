import streamlit as st


MENU_ITEMS = [
    "Dashboard",
    "Inventaris & Gudang",
    "Penjualan & Distribusi",
    "Pembelian & Supplier",
    "Keuangan & Akuntansi",
    "Wilayah / Rayon",
    "Laporan & Dokumen",
]


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            "<div style='font-size:30px;font-weight:800'>🌱 SuperTani</div>",
            unsafe_allow_html=True,
        )
        st.caption("ERP · BUSINESS MANAGEMENT")
        st.divider()
        st.markdown("**WORKSPACE**")
        selected_menu = st.radio(
            "Navigasi",
            MENU_ITEMS,
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("SUPERTANI ERP · BASIC 0.2")
        st.caption("Mode data: sementara / sesi")

    return selected_menu
