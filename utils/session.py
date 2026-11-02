import streamlit as st


def initialize_session():
    """Menyiapkan wadah data sementara untuk sesi aplikasi."""
    defaults = {
        "products": [],
        "customers": [],
        "suppliers": [],
        "warehouses": [],
        "areas": [],
        "stock_movements": [],
        "purchase_orders": [],
        "sales_orders": [],
        "delivery_orders": [],
        "invoices": [],
        "cash_transactions": [],
        "journal_entries": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy()
