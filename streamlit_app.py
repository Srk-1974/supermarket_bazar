import os

import pandas as pd
import psycopg2
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()


def get_setting(name, default=None):
    try:
        value = st.secrets.get(name, default)
        if value is not None:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


st.set_page_config(page_title="Supermarket Bazaar", page_icon="🛒", layout="wide")

components.html(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #091c2b 0%, #0f2942 35%, #1c5d90 100%);
            color: #edf6ff;
        }
        .main .block-container {
            padding-top: 2.2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        .brand-card {
            background: rgba(12, 29, 45, 0.7);
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 24px;
            padding: 1.5rem 1.8rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        }
        .brand-box {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }
        .icon-box {
            width: 110px;
            height: 110px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(180deg, #f9d96f 0%, #f4b019 100%);
            border-radius: 18px;
            box-shadow: 0 0 28px rgba(246, 193, 70, 0.8);
            border: 2px solid rgba(255,255,255,0.65);
        }
        .icon-box span {
            font-size: 58px;
        }
        .brand-title {
            margin: 0;
            color: #f5f8ff;
            font-size: clamp(2.3rem, 4vw, 4rem);
            font-weight: 800;
            letter-spacing: 0.05em;
            line-height: 1.05;
        }
        .brand-sub {
            color: rgba(255,255,255,0.8);
            font-size: 1.15rem;
            margin-top: 0.35rem;
        }
        .panel {
            background: rgba(11, 29, 46, 0.82);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 24px;
            padding: 1.2rem 1.3rem 1.1rem 1.3rem;
            margin-bottom: 1.4rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.12);
        }
        .panel h2 {
            margin: 0 !important;
            color: white !important;
            font-size: 2rem !important;
            font-weight: 800 !important;
        }
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.8rem;
        }
        .stButton > button {
            background: #2f82ff;
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            padding: 0.68rem 1.1rem;
        }
        .stButton > button:hover {
            background: #1f72f1;
        }
        .status-text {
            color: rgba(255,255,255,0.8);
            font-size: 1.05rem;
            margin: 0.3rem 0 0.9rem 0;
        }
        .table-wrap .stDataFrame {
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            overflow: hidden;
        }
        .db-form .stSelectbox label, .db-form .stTextInput label {
            color: white !important;
            font-weight: 600;
        }
        .db-form .stTextInput input, .db-form .stSelectbox select {
            background: rgba(255,255,255,0.04);
            color: white;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 10px;
        }
    </style>

    <div class="brand-card">
      <div class="brand-box">
        <div class="icon-box"><span>🛒</span></div>
        <div>
          <h1 class="brand-title">SUPERMARKET_BAZAAR</h1>
          <div class="brand-sub">Store dashboard for products and sales</div>
        </div>
      </div>
    </div>
    """,
    height=180,
)

with st.sidebar:
    st.header("Database Settings")
    db_type = st.selectbox("Database type", ["postgresql", "mysql", "sqlserver", "mongodb"])
    host = st.text_input("Host", value=get_setting("DB_HOST", "localhost"))
    port = st.text_input("Port", value=get_setting("DB_PORT", "5432"))
    db_name = st.text_input("Database", value=get_setting("DB_NAME", "supermarketdb"))
    user = st.text_input("User", value=get_setting("DB_USER", "postgres"))
    password = st.text_input("Password", type="password", value=get_setting("DB_PASSWORD", "postgres"))
    connect_btn = st.button("Connect")

if not host or not db_name or not user:
    st.warning("Set the database connection values before connecting. For public deployment, use Streamlit secrets or environment variables instead of localhost.")

sample_data = pd.DataFrame(
    [
        {"product_id": 1, "sku": "SKU-1001", "name": "Fresh Apples", "retail_price": 2.49, "is_active": True},
        {"product_id": 2, "sku": "SKU-1002", "name": "Organic Milk", "retail_price": 3.99, "is_active": True},
        {"product_id": 3, "sku": "SKU-1003", "name": "Bread Loaf", "retail_price": 4.25, "is_active": False},
    ]
)

st.markdown(
    """
    <div class="panel">
      <div class="section-header">
        <h2>Products</h2>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

prod_col, btn_col = st.columns([4, 1])
with prod_col:
    st.markdown('<div class="status-text">Ready</div>', unsafe_allow_html=True)
with btn_col:
    if st.button("Load products"):
        connect_btn = True

if connect_btn:
    if db_type != "postgresql":
        st.warning("This public demo is configured for PostgreSQL. For MySQL, SQL Server, or MongoDB, update the connection logic before deployment.")
    try:
        conn = psycopg2.connect(
            host=host,
            port=int(port) if str(port).strip() else 5432,
            dbname=db_name,
            user=user,
            password=password,
        )
        cur = conn.cursor()
        cur.execute("SELECT product_id, sku, name, retail_price, is_active FROM products ORDER BY product_id LIMIT 20")
        rows = cur.fetchall()
        columns = ["product_id", "sku", "name", "retail_price", "is_active"]
        df = pd.DataFrame(rows, columns=columns)
        cur.close()
        conn.close()
        st.markdown('<div class="table-wrap">', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Connection failed: {exc}\n\nHint: public deployments cannot use localhost. Use a hosted database and set DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD in Streamlit secrets.")
        st.info("Showing sample data until a public database is connected.")
        st.dataframe(sample_data, use_container_width=True)
else:
    st.markdown('<div class="table-wrap">', unsafe_allow_html=True)
    st.dataframe(sample_data, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="panel">
      <div class="section-header">
        <h2>Database Configuration</h2>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="db-form">', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    db_type2 = st.selectbox("Database type", ["postgresql", "mysql", "sqlserver", "mongodb"], index=["postgresql", "mysql", "sqlserver", "mongodb"].index(db_type))
with c2:
    host2 = st.text_input("Host", value=host)
with c3:
    port2 = st.text_input("Port", value=port)

c4, c5, c6 = st.columns(3)
with c4:
    db_name2 = st.text_input("Database", value=db_name)
with c5:
    user2 = st.text_input("User", value=user)
with c6:
    password2 = st.text_input("Password", type="password", value=password)

st.markdown('</div>', unsafe_allow_html=True)

if st.button("Test connection"):
    st.info("Use the database settings above to connect to your hosted PostgreSQL instance.")

st.subheader("Quick Actions")
col1, col2 = st.columns(2)
with col1:
    st.metric("Products", "Live DB")
with col2:
    st.metric("Status", "Ready")
