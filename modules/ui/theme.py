APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: "DM Sans", sans-serif;
    color: #111111 !important;
}

.stApp {
    color: #111111 !important;
    background: #f4f7f5 !important;
}

/* Default text is dark on the light application canvas. */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stApp h6, .stApp p, .stApp label, .stApp caption, .stApp span,
[data-testid="stMarkdownContainer"] {
    color: #111111 !important;
}

[data-testid="stHeader"] {
    background: #ffffff !important;
}

.block-container {
    max-width: 1500px;
    padding: 1.25rem 2rem 2rem;
    color: #111111 !important;
}

[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e7e4;
}

[data-testid="stSidebar"] * {
    color: #111111 !important;
}

[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 0.15rem;
}

[data-testid="stSidebar"] [role="radio"] {
    min-height: 34px;
    padding: 4px 8px;
    border-radius: 8px;
}

[data-testid="stSidebar"] hr {
    border-color: #e2e7e4 !important;
}

[data-testid="stMetric"] {
    padding: 18px;
    border: 1px solid #e4ebe6;
    border-radius: 12px;
    background: #ffffff;
    box-shadow: 0 1px 2px rgba(20, 50, 40, 0.02);
}

[data-testid="stMetricLabel"] {
    color: #718078 !important;
    font-size: 0.78rem !important;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: #173d32 !important;
    font-size: 1.55rem !important;
    font-weight: 800;
}

[data-testid="stMetricDelta"] {
    color: #5d836f !important;
}

.stButton > button {
    border-radius: 9px;
    font-weight: 600;
}

[data-testid="stExpander"] {
    border: 1px solid #e4ebe6;
    border-radius: 12px;
    background: #ffffff;
}

[data-testid="stDataFrame"] {
    overflow: hidden;
    border: 1px solid #e4ebe6;
    border-radius: 12px;
}

/* Use visible borders on the actual widget roots across Streamlit versions. */
[data-testid="stTextInputRootElement"],
[data-testid="stNumberInputContainer"],
[data-testid="stTextAreaRootElement"],
[data-baseweb="input"],
[data-baseweb="textarea"] {
    border: 1.5px solid #b8860b !important;
    border-radius: 8px !important;
    background-color: #ffffff !important;
}

[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stTextAreaRootElement"]:focus-within,
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within {
    border-color: #111111 !important;
    box-shadow: 0 0 0 2px rgba(184, 134, 11, 0.2) !important;
}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    caret-color: #111111 !important;
    background-color: #ffffff !important;
}

[data-baseweb="input"],
[data-baseweb="textarea"] {
    border-color: #d8dfda !important;
    background-color: #ffffff !important;
}

[data-testid="stTextInput"] input::placeholder,
[data-testid="stNumberInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #7b8580 !important;
    -webkit-text-fill-color: #7b8580 !important;
}

[data-baseweb="select"] > div,
[data-baseweb="select"] span {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

[data-baseweb="select"] > div {
    border-color: #d8dfda !important;
    background-color: #ffffff !important;
}

ul[role="listbox"] {
    background: #ffffff !important;
}

ul[role="listbox"] li,
ul[role="listbox"] li * {
    color: #111111 !important;
}

[data-testid="stNumberInput"] button,
[data-testid="stNumberInput"] button svg {
    color: #111111 !important;
    fill: #111111 !important;
}

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    color: #111111 !important;
    background: #ffffff !important;
    border: 1px solid #d8dfda !important;
}

[data-testid="stExpander"] button,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * {
    color: #111111 !important;
}

/* Data tables: dark header with white text, light body with dark text. */
[data-testid="stDataFrame"] thead,
[data-testid="stDataFrame"] thead * {
    color: #ffffff !important;
    background-color: #111111 !important;
}

[data-testid="stDataFrame"] tbody,
[data-testid="stDataFrame"] tbody * {
    color: #111111 !important;
}

.stAlert[data-baseweb="notification"] * {
    color: inherit !important;
}
</style>
"""
