
import streamlit as st
import pandas as pd
from modules.services.finance_service import (
    load_master, init_state, add_transaction, get_summary,
    get_account_balances, filter_transactions
)

def rupiah(value):
    return "Rp " + f"{int(round(value)):,.0f}".replace(",", ".")

def render_finance():
    st.title("💰 Keuangan & Akuntansi")
    st.caption("SuperTani ERP · Pencatatan kas, bank, dan arus keuangan")
    master = load_master()
    init_state(master)

    transactions = st.session_state.finance_transactions
    summary = get_summary(transactions)
    balances = get_account_balances(master, transactions)
    summary["total_balance"] = sum(item["balance"] for item in balances)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Saldo", rupiah(summary["total_balance"]))
    c2.metric("Pemasukan", rupiah(summary["income"]))
    c3.metric("Pengeluaran", rupiah(summary["expense"]))
    c4.metric("Surplus Kas", rupiah(summary["income"] - summary["expense"]))

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard", "➕ Input Transaksi", "🏦 Kas & Bank", "📑 Riwayat & Ekspor"
    ])

    with tab1:
        st.subheader("Ringkasan Arus Kas")
        if transactions:
            df = pd.DataFrame(transactions)
            df["tanggal"] = pd.to_datetime(df["tanggal"])
            monthly = df.assign(bulan=df["tanggal"].dt.strftime("%Y-%m")).pivot_table(
                index="bulan", columns="jenis", values="jumlah", aggfunc="sum", fill_value=0
            )
            for col in ["Pemasukan", "Pengeluaran"]:
                if col not in monthly.columns:
                    monthly[col] = 0
            st.bar_chart(monthly[["Pemasukan", "Pengeluaran"]])
        else:
            st.info("Belum ada transaksi. Tambahkan transaksi pertama melalui tab Input Transaksi.")
        st.subheader("Transaksi Terbaru")
        if transactions:
            latest = sorted(transactions, key=lambda x: (x["tanggal"], x["created_at"]), reverse=True)[:8]
            view = pd.DataFrame(latest)[["tanggal", "jenis", "kategori", "keterangan", "akun", "jumlah"]]
            view["jumlah"] = view.apply(
                lambda r: ("+" if r["jenis"] == "Pemasukan" else "-") + rupiah(r["jumlah"]), axis=1
            )
            st.dataframe(view, use_container_width=True, hide_index=True)
        else:
            st.caption("Belum ada data untuk ditampilkan.")

    with tab2:
        st.subheader("Catat Transaksi Baru")
        with st.form("finance_transaction_form", clear_on_submit=True):
            a, b = st.columns(2)
            jenis = a.selectbox("Jenis transaksi", ["Pemasukan", "Pengeluaran"])
            tanggal = b.date_input("Tanggal")
            kategori_list = master["categories"][jenis]
            kategori = st.selectbox("Kategori", kategori_list)
            akun = st.selectbox("Sumber / tujuan akun", [x["name"] for x in master["accounts"]])
            keterangan = st.text_input("Keterangan", placeholder="Contoh: Penjualan pupuk NPK")
            d, e = st.columns(2)
            jumlah = d.number_input("Nominal (Rp)", min_value=0, step=10000, value=0)
            referensi = e.text_input("No. referensi (opsional)")
            catat = st.form_submit_button("Simpan Transaksi", type="primary", use_container_width=True)
            if catat:
                if jumlah <= 0:
                    st.error("Nominal harus lebih besar dari nol.")
                elif not keterangan.strip():
                    st.error("Keterangan transaksi wajib diisi.")
                else:
                    add_transaction(
                        jenis=jenis, tanggal=tanggal.isoformat(), kategori=kategori,
                        akun=akun, keterangan=keterangan.strip(), jumlah=int(jumlah),
                        referensi=referensi.strip()
                    )
                    st.success("Transaksi berhasil dicatat.")
                    st.rerun()

    with tab3:
        st.subheader("Saldo Kas & Bank")
        if balances:
            cols = st.columns(min(3, len(balances)))
            for i, item in enumerate(balances):
                with cols[i % len(cols)]:
                    st.metric(item["name"], rupiah(item["balance"]))
        st.caption("Saldo dihitung dari saldo awal akun ditambah pemasukan dan dikurangi pengeluaran.")

    with tab4:
        st.subheader("Riwayat Transaksi")
        f1, f2 = st.columns(2)
        jenis_filter = f1.selectbox("Filter jenis", ["Semua", "Pemasukan", "Pengeluaran"])
        keyword = f2.text_input("Cari keterangan / kategori")
        filtered = filter_transactions(transactions, jenis_filter, keyword)
        if filtered:
            df = pd.DataFrame(filtered)
            df = df[["tanggal", "jenis", "kategori", "keterangan", "akun", "referensi", "jumlah"]]
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Unduh CSV", csv, "supertani_transaksi_keuangan.csv", "text/csv")
        else:
            st.info("Tidak ada transaksi yang cocok dengan filter.")

    st.divider()
    st.caption("Mode Basic: transaksi tersimpan di session aplikasi. Data dapat hilang saat sesi berakhir atau aplikasi dimulai ulang.")
