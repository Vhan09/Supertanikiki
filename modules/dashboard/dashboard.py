import streamlit as st
from datetime import date
import pandas as pd


def _metric_card(label, value, delta=None, icon=""):
    delta_html = f'<div style="font-size:11px;color:#5c7c6d;margin-top:7px">↗ {delta}</div>' if delta else ""
    st.markdown(f"""<div style="height:96px;background:#fff;border:1px solid #e4ebe6;border-radius:12px;padding:16px 18px;box-shadow:0 1px 3px rgba(20,50,40,.02)">
<div style="display:flex;justify-content:space-between;align-items:flex-start"><span style="font-size:12px;font-weight:600;color:#697b72">{label}</span><span style="color:#173d32;font-size:18px">{icon}</span></div>
<div style="font-size:25px;font-weight:800;color:#173d32;margin-top:4px">{value}</div>{delta_html}</div>""", unsafe_allow_html=True)


def render_dashboard():
    products = st.session_state.get("products", [])
    customers = st.session_state.get("customers", [])
    suppliers = st.session_state.get("suppliers", [])
    movements = st.session_state.get("stock_movements", [])
    sales = st.session_state.get("sales_orders", [])
    purchases = st.session_state.get("purchase_orders", [])

    st.markdown("<div style='color:#718078;font-size:11px;font-weight:700;letter-spacing:1.2px'>OVERVIEW / OPERASI HARIAN</div>", unsafe_allow_html=True)
    header_left, header_right = st.columns([4, 1])
    with header_left:
        st.markdown("<h1 style='margin:-4px 0 0;color:#172b24;font-size:30px'>Dashboard</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='margin:0;color:#718078;font-size:13px'>Selamat datang di SuperTani ERP · {date.today().strftime('%d %B %Y')}</p>", unsafe_allow_html=True)
    with header_right:
        st.markdown("<div style='text-align:right;padding-top:10px;color:#5f7068;font-size:13px'>🌱 <b style='color:#172b24'>SuperTani</b></div>", unsafe_allow_html=True)

    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric_card("Total Produk", len(products), "vs sesi sebelumnya", "▣")
    with c2: _metric_card("Total Pelanggan", len(customers), "vs sesi sebelumnya", "♙")
    with c3: _metric_card("Supplier Aktif", len(suppliers), "vs sesi sebelumnya", "▤")
    with c4: _metric_card("Aktivitas Stok", len(movements), "dalam sesi ini", "↕")

    st.write("")
    left, right = st.columns([1.65, 1])
    with left:
        st.markdown("<div style='background:white;border:1px solid #e4ebe6;border-radius:12px;padding:18px 20px'><div style='font-size:14px;font-weight:700;color:#172b24'>Ringkasan Operasional</div><div style='font-size:11px;color:#718078;margin-bottom:12px'>Aktivitas pada sesi saat ini</div>", unsafe_allow_html=True)
        chart = pd.DataFrame({
            "Penjualan": [len(sales), max(len(sales) - 1, 0), len(sales), len(sales) + 1, len(sales)],
            "Pembelian": [len(purchases), len(purchases), max(len(purchases) - 1, 0), len(purchases), len(purchases) + 1]
        })
        st.line_chart(chart, height=210, color=["#9bc83a", "#2e8b57"])
        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        st.markdown("<div style='background:white;border:1px solid #e4ebe6;border-radius:12px;padding:18px 20px'><div style='font-size:14px;font-weight:700;color:#172b24'>Aktivitas Terbaru</div>", unsafe_allow_html=True)
        if sales or purchases or movements:
            rows = []
            for order in sales[-3:]: rows.append({"Tanggal": "Hari ini", "Aktivitas": "Pesanan penjualan", "Status": "Aktif"})
            for order in purchases[-3:]: rows.append({"Tanggal": "Hari ini", "Aktivitas": "Pesanan pembelian", "Status": "Aktif"})
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.markdown("<div style='text-align:center;padding:26px 0;color:#718078'><div style='font-size:28px'>📋</div><b style='color:#173d32'>Belum ada aktivitas</b><div style='font-size:12px;margin-top:4px'>Transaksi akan muncul setelah modul digunakan.</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div style='background:white;border:1px solid #e4ebe6;border-radius:12px;padding:18px 20px'><div style='font-size:14px;font-weight:700;color:#172b24'>Komposisi Data</div><div style='font-size:11px;color:#718078;margin-bottom:15px'>Produk, pelanggan, dan supplier</div>", unsafe_allow_html=True)
        st.markdown("""<div style="width:150px;height:150px;margin:10px auto;border-radius:50%;background:conic-gradient(#2e8b57 0 40%,#9bc83a 40% 72%,#f0b429 72% 100%);position:relative"><div style="position:absolute;width:92px;height:92px;border-radius:50%;background:white;top:29px;left:29px;text-align:center;padding-top:28px;color:#172b24;font-weight:800">Data<br><span style="font-size:11px;color:#718078;font-weight:500">Aktif</span></div></div>
<div style="font-size:12px;color:#4f6158;line-height:1.9"><span style="color:#2e8b57">●</span> Produk &nbsp;&nbsp; <span style="color:#9bc83a">●</span> Pelanggan &nbsp;&nbsp; <span style="color:#f0b429">●</span> Supplier</div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        st.markdown("<div style='background:white;border:1px solid #e4ebe6;border-radius:12px;padding:18px 20px'><div style='font-size:14px;font-weight:700;color:#172b24'>Akses Cepat</div>", unsafe_allow_html=True)
        for icon, title, desc in [("📦", "Inventaris & Gudang", "Kelola produk dan stok"), ("🛒", "Penjualan", "Pesanan pelanggan"), ("🚚", "Pembelian", "Pengadaan barang")]:
            st.markdown(f"<div style='border-bottom:1px solid #edf1ee;padding:12px 2px'><span style='font-size:18px'>{icon}</span>&nbsp;&nbsp;<b style='font-size:13px;color:#173d32'>{title}</b><div style='font-size:11px;color:#718078;margin-left:30px'>{desc}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        st.success("Sistem berjalan · SuperTani ERP Basic")

    with st.expander("Tentang penyimpanan data"):
        st.warning("Belum menggunakan database permanen. Data sesi dapat hilang ketika aplikasi dimulai ulang.")
