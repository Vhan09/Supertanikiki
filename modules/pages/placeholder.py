import streamlit as st


def render_placeholder(menu: str) -> None:
    st.markdown(
        """
        <div style="color:#718078;font-size:12px;font-weight:700;letter-spacing:1px">
            SUPERTANI ERP / WORKSPACE
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title(menu)
    st.info(
        "Kerangka halaman sudah aktif. Fitur transaksi modul ini akan "
        "diimplementasikan berikutnya."
    )
    st.caption("Versi Basic: data hanya tersimpan sementara selama sesi aplikasi.")
