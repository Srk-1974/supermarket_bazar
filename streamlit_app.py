import os

import pandas as pd
import psycopg2
import streamlit as st
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

st.title("SUPERMARKET_BAZAAR")
st.caption("Connected database dashboard")

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

        st.success("Connected successfully")
        st.dataframe(df, use_container_width=True)
    except Exception as exc:
        st.error(f"Connection failed: {exc}\n\nHint: public deployments cannot use localhost. Use a hosted database and set DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD in Streamlit secrets.")
        st.info("Showing sample data until a public database is connected.")
        st.dataframe(sample_data, use_container_width=True)
else:
    st.info("Use the sidebar to configure your database and click Connect. For public deployment, use a hosted database instead of localhost.")
    st.dataframe(sample_data, use_container_width=True)

st.subheader("Quick Actions")
col1, col2 = st.columns(2)
with col1:
    st.metric("Products", "Live DB")
with col2:
    st.metric("Status", "Ready")
