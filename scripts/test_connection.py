#!/usr/bin/env python3
"""Simple DB connectivity test script.
Reads POSTGRES_URL or DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD from environment or .env
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

POSTGRES_URL = os.getenv('POSTGRES_URL')
DB_ENGINE = os.getenv('DB_ENGINE', 'postgres')

if DB_ENGINE != 'postgres':
    print('This test script currently supports PostgreSQL only. Set DB_ENGINE=postgres or use POSTGRES_URL.')

if not POSTGRES_URL:
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    name = os.getenv('DB_NAME', 'supermarketdb')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '')
    POSTGRES_URL = f"postgresql://{user}:{password}@{host}:{port}/{name}"

print('Attempting to connect to:', POSTGRES_URL)

try:
    import psycopg2
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()
    cur.execute('SELECT version();')
    ver = cur.fetchone()
    print('Connected. Postgres version:', ver[0])
    cur.close()
    conn.close()
    sys.exit(0)
except Exception as e:
    print('Connection failed:', str(e))
    sys.exit(2)
