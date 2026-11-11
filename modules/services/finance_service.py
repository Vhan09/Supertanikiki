
import json
from pathlib import Path
from datetime import datetime
import streamlit as st

MASTER_PATH = Path(__file__).resolve().parents[2] / "data" / "finance_master.json"

def load_master():
    with open(MASTER_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

def init_state(master):
    if "finance_transactions" not in st.session_state:
        st.session_state.finance_transactions = []
    if "finance_next_id" not in st.session_state:
        st.session_state.finance_next_id = 1

def add_transaction(jenis, tanggal, kategori, akun, keterangan, jumlah, referensi=""):
    record = {
        "id": st.session_state.finance_next_id,
        "tanggal": tanggal,
        "jenis": jenis,
        "kategori": kategori,
        "akun": akun,
        "keterangan": keterangan,
        "jumlah": int(jumlah),
        "referensi": referensi,
        "created_at": datetime.now().isoformat(timespec="seconds")
    }
    st.session_state.finance_transactions.append(record)
    st.session_state.finance_next_id += 1

def get_summary(transactions):
    income = sum(t["jumlah"] for t in transactions if t["jenis"] == "Pemasukan")
    expense = sum(t["jumlah"] for t in transactions if t["jenis"] == "Pengeluaran")
    return {
        "income": income,
        "expense": expense,
        "total_balance": income - expense
    }

def get_account_balances(master, transactions):
    results = []
    for account in master["accounts"]:
        balance = int(account.get("opening_balance", 0))
        for t in transactions:
            if t["akun"] == account["name"]:
                balance += t["jumlah"] if t["jenis"] == "Pemasukan" else -t["jumlah"]
        results.append({"name": account["name"], "balance": balance})
    return results

def filter_transactions(transactions, jenis_filter="Semua", keyword=""):
    result = transactions
    if jenis_filter != "Semua":
        result = [t for t in result if t["jenis"] == jenis_filter]
    term = keyword.strip().lower()
    if term:
        result = [
            t for t in result
            if term in t["keterangan"].lower() or term in t["kategori"].lower()
        ]
    return sorted(result, key=lambda t: (t["tanggal"], t["id"]), reverse=True)
