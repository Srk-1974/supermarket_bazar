import os
import sys
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

load_dotenv()

app = Flask(__name__)

ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')
DB_TYPES = ['postgresql', 'mysql', 'sqlserver', 'mongodb']


def get_db_url(db_type='postgresql', user='postgres', password='postgres', host='localhost', port='5432', db='supermarketdb'):
    if db_type == 'postgresql':
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    if db_type == 'mysql':
        return f"mysql://{user}:{password}@{host}:{port}/{db}"
    if db_type == 'sqlserver':
        return f"mssql://{user}:{password}@{host}:{port}/{db}?driver=ODBC+Driver+17+for+SQL+Server"
    if db_type == 'mongodb':
        return f"mongodb://{user}:{password}@{host}:{port}/{db}"
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def get_db_config():
    db_type = os.getenv('DB_TYPE', 'postgresql').lower()
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'postgres')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    db = os.getenv('DB_NAME', 'supermarketdb')
    return {
        'type': db_type if db_type in DB_TYPES else 'postgresql',
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'db': db,
        'url': os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL') or get_db_url(db_type, user, password, host, port, db)
    }


def save_db_config(config):
    config = config or {}
    db_type = (config.get('type') or os.getenv('DB_TYPE', 'postgresql')).lower()
    if db_type not in DB_TYPES:
        db_type = 'postgresql'

    values = {
        'DB_TYPE': db_type,
        'DB_USER': str(config.get('user') or os.getenv('DB_USER', 'postgres')),
        'DB_PASSWORD': str(config.get('password') or os.getenv('DB_PASSWORD', 'postgres')),
        'DB_HOST': str(config.get('host') or os.getenv('DB_HOST', 'localhost')),
        'DB_PORT': str(config.get('port') or os.getenv('DB_PORT', '5432')),
        'DB_NAME': str(config.get('db') or os.getenv('DB_NAME', 'supermarketdb')),
    }
    values['POSTGRES_URL'] = get_db_url(
        db_type,
        values['DB_USER'],
        values['DB_PASSWORD'],
        values['DB_HOST'],
        values['DB_PORT'],
        values['DB_NAME']
    )
    values['DATABASE_URL'] = values['POSTGRES_URL']

    existing = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                existing[key.strip()] = value.strip()

    existing.update(values)

    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        for key in ['DB_TYPE', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'POSTGRES_URL', 'DATABASE_URL']:
            f.write(f"{key}={existing.get(key, '')}\n")

    os.environ.update(values)
    app.config['POSTGRES_URL'] = values['POSTGRES_URL']
    app.config['DB_TYPE'] = db_type
    return values


app.config['POSTGRES_URL'] = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL') or get_db_url(
    os.getenv('DB_TYPE', 'postgresql'),
    os.getenv('DB_USER', 'postgres'),
    os.getenv('DB_PASSWORD', 'postgres'),
    os.getenv('DB_HOST', 'localhost'),
    os.getenv('DB_PORT', '5432'),
    os.getenv('DB_NAME', 'supermarketdb')
)
app.config['DB_TYPE'] = os.getenv('DB_TYPE', 'postgresql').lower()


def get_conn():
    config = get_db_config()
    db_type = config['type']

    if db_type == 'postgresql':
        return psycopg2.connect(config['url'])

    if db_type == 'mysql':
        import pymysql
        return pymysql.connect(
            host=config['host'],
            port=int(config['port']),
            user=config['user'],
            password=config['password'],
            database=config['db']
        )

    if db_type == 'mongodb':
        from pymongo import MongoClient
        return MongoClient(config['url'])

    if db_type == 'sqlserver':
        raise ValueError('SQL Server driver is not configured in this app yet. Please keep the app on PostgreSQL or install the required SQL Server client package.')

    return psycopg2.connect(config['url'])


def ensure_sql_database_ready():
    config = get_db_config()
    db_type = config['type']
    if db_type not in {'postgresql', 'mysql'}:
        raise ValueError(
            f"This dashboard currently supports PostgreSQL/MySQL SQL queries. The configured database type '{db_type}' is saved, but the app logic is still PostgreSQL-based."
        )

    try:
        conn = get_conn()
        if hasattr(conn, 'cursor'):
            cur = conn.cursor()
            cur.execute('SELECT 1')
            cur.close()
        conn.close()
        return True
    except Exception as exc:
        raise RuntimeError(
            f"Database connection failed for {db_type} at {config['host']}:{config['port']}/{config['db']}. Start the database server or change the connection settings. Details: {exc}"
        )

@app.route('/')
def index():
    return render_template('index.html', db_config=get_db_config())


@app.route('/config', methods=['GET', 'POST'])
def configure_database():
    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        try:
            values = save_db_config({
                'type': payload.get('type'),
                'user': payload.get('user'),
                'password': payload.get('password'),
                'host': payload.get('host'),
                'port': payload.get('port'),
                'db': payload.get('db')
            })
            return jsonify({
                'status': 'ok',
                'message': 'Database configuration saved successfully.',
                'config': {
                    'type': values['DB_TYPE'],
                    'host': values['DB_HOST'],
                    'port': values['DB_PORT'],
                    'db': values['DB_NAME'],
                    'user': values['DB_USER'],
                    'password': values['DB_PASSWORD']
                }
            }), 200
        except Exception as exc:
            return jsonify({'status': 'error', 'message': str(exc)}), 500

    return jsonify(get_db_config()), 200

@app.route('/health')
def health():
    config = get_db_config()
    try:
        ensure_sql_database_ready()
        return jsonify({'status': 'ok', 'db_type': config['type'], 'database': config['db']}), 200
    except Exception as exc:
        return jsonify({'status': 'degraded', 'db_type': config['type'], 'database': config['db'], 'error': str(exc)}), 503


@app.route('/test-connection', methods=['POST'])
def test_connection():
    payload = request.get_json(silent=True) or {}
    try:
        values = save_db_config({
            'type': payload.get('type'),
            'user': payload.get('user'),
            'password': payload.get('password'),
            'host': payload.get('host'),
            'port': payload.get('port'),
            'db': payload.get('db')
        })
        ensure_sql_database_ready()
        return jsonify({
            'status': 'ok',
            'message': 'Database connection is valid.',
            'config': {
                'type': values['DB_TYPE'],
                'host': values['DB_HOST'],
                'port': values['DB_PORT'],
                'db': values['DB_NAME'],
                'user': values['DB_USER'],
            }
        }), 200
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 503


@app.route('/apply-schema', methods=['POST'])
def apply_schema():
    """Apply SQL schema located at db/schema_postgres.sql and seed file db/seed_sample.sql
    Call with POST /apply-schema (no body)"""
    schema_path = os.path.join(os.path.dirname(__file__), 'db', 'schema_postgres.sql')
    seed_path = os.path.join(os.path.dirname(__file__), 'db', 'seed_sample.sql')
    try:
        conn = get_conn()
        cur = conn.cursor()
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_text = f.read()
            cur.execute(sql_text)
            conn.commit()
        with open(seed_path, 'r', encoding='utf-8') as f:
            seed_text = f.read()
            cur.execute(seed_text)
            conn.commit()
        cur.close()
        conn.close()
        return jsonify({'applied': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products', methods=['GET'])
def list_products():
    try:
        ensure_sql_database_ready()
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT product_id, sku, name, retail_price, is_active FROM products ORDER BY product_id LIMIT 100')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({'error': str(e), 'hint': 'Start PostgreSQL (or another supported SQL server), then apply the schema in db/schema_postgres.sql.'}), 503

@app.route('/sales', methods=['POST'])
def create_sale():
    payload = request.json or {}
    # Minimal creation: expects location_id, cashier_id, lines [{product_id, quantity}]
    location_id = payload.get('location_id')
    cashier_id = payload.get('cashier_id')
    customer_id = payload.get('customer_id')
    lines = payload.get('lines', [])
    if not lines or not location_id or not cashier_id:
        return jsonify({'error': 'location_id, cashier_id and lines required'}), 400
    try:
        ensure_sql_database_ready()
        conn = get_conn()
        cur = conn.cursor()
        # Start transaction
        cur.execute('BEGIN;')
        # create sale header
        cur.execute("INSERT INTO sales (sale_number, location_id, cashier_id, customer_id, subtotal, total, status) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING sale_id",
                    (f"INV-LOCAL-{os.getpid()}-{int(os.times()[4])}", location_id, cashier_id, customer_id, 0, 0, 'PENDING'))
        sale_id = cur.fetchone()[0]
        subtotal = 0
        for ln in lines:
            pid = ln.get('product_id')
            qty = float(ln.get('quantity', 1))
            # get product price and cost
            cur.execute('SELECT retail_price, cost_price, sku, name FROM products WHERE product_id=%s', (pid,))
            prod = cur.fetchone()
            if not prod:
                conn.rollback()
                return jsonify({'error': f'product {pid} not found'}), 400
            retail_price = prod[0]
            cost_price = prod[1]
            sku = prod[2]
            desc = prod[3]
            line_total = retail_price * qty
            subtotal += line_total
            cur.execute("INSERT INTO sale_lines (sale_id, product_id, location_id, sku_snapshot, description_snapshot, quantity, unit_price, unit_cost, line_total) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (sale_id, pid, location_id, sku, desc, qty, retail_price, cost_price, line_total))
            # create inventory movement and decrement on hand
            cur.execute("INSERT INTO inventory_movements (product_id, location_id, movement_type, quantity, unit_cost) VALUES (%s,%s,%s,%s,%s)",
                        (pid, location_id, 'SALE', qty, cost_price))
            # update inventory: decrement qty_on_hand (simple approach)
            cur.execute('UPDATE inventory SET qty_on_hand = qty_on_hand - %s, last_updated_at = now() WHERE product_id=%s AND location_id=%s', (qty, pid, location_id))
        # update sale totals and mark completed
        cur.execute('UPDATE sales SET subtotal=%s, total=%s, status=%s WHERE sale_id=%s', (subtotal, subtotal, 'COMPLETED', sale_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'sale_id': sale_id, 'subtotal': subtotal}), 201
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        return jsonify({'error': str(e), 'hint': 'The selected database must be a valid PostgreSQL/MySQL instance with the schema from db/schema_postgres.sql.'}), 503

if __name__ == '__main__':
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', '8000'))
    active_url = app.config.get('POSTGRES_URL') or get_db_config()['url']
    print(f'Listening on {host}:{port} - connecting to DB: {active_url}')
    app.run(host=host, port=port)
