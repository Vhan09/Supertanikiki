import streamlit as st
from datetime import date


def render_dashboard():
    st.title("🌱 SuperTani ERP")
    st.subheader("Dashboard Operasional")
    st.caption(f"Ringkasan aktivitas · {date.today().strftime('%d-%m-%Y')}")

    products = st.session_state.get("products", [])
    customers = st.session_state.get("customers", [])
    suppliers = st.session_state.get("suppliers", [])
    stock_movements = st.session_state.get("stock_movements", [])
    sales_orders = st.session_state.get("sales_orders", [])
    purchase_orders = st.session_state.get("purchase_orders", [])

    c1, c2, c3 = st.columns(3)
    c1.metric("Master Produk", len(products))
    c2.metric("Pelanggan", len(customers))
    c3.metric("Supplier", len(suppliers))

    c4, c5, c6 = st.columns(3)
    c4.metric("Mutasi Stok", len(stock_movements))
    c5.metric("Sales Order", len(sales_orders))
    c6.metric("Purchase Order", len(purchase_orders))

    st.divider()
    st.subheader("Aktivitas Terbaru")
    if stock_movements or sales_orders or purchase_orders:
        st.write("Aktivitas akan ditampilkan di sini setelah modul transaksi dibuat.")
    else:
        st.info("Belum ada aktivitas. Mulai dengan menyiapkan master produk dan gudang.")

    with st.expander("Catatan versi Basic"):
        st.markdown(
            """
            - Data transaksi hanya berada di sesi aplikasi.
            - Data dapat hilang ketika sesi berakhir atau aplikasi dimulai ulang.
            - Belum ada database permanen.
            - Modul akan dikembangkan bertahap dan saling terhubung.
            """
        )
