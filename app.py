import streamlit as st

from config import APP_ICON, APP_NAME
from modules.dashboard.dashboard import render_dashboard
from modules.inventory.Inventory import render_inventaris_page
from modules.pages.placeholder import render_placeholder
from modules.ui.navigation import render_sidebar
from modules.ui.theme import APP_CSS
from utils.session import initialize_session


def configure_app() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon=APP_ICON, layout="wide")
    st.markdown(APP_CSS, unsafe_allow_html=True)
    initialize_session()


def main() -> None:
    configure_app()
    selected_menu = render_sidebar()

    if selected_menu == "Dashboard":
        render_dashboard()
    elif selected_menu == "Inventaris & Gudang":
        render_inventaris_page()
    else:
        render_placeholder(selected_menu)


if __name__ == "__main__":
    main()
