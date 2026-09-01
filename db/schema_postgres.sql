-- PostgreSQL schema for Supermarket/Bazaar Management System

-- Optional: enable uuid generation
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- For gen_random_uuid() (Postgres 13+ with pgcrypto):
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Locations: stores / warehouses / outlets
CREATE TABLE IF NOT EXISTS locations (
  location_id BIGSERIAL PRIMARY KEY,
  location_uuid UUID UNIQUE DEFAULT gen_random_uuid(),
  name VARCHAR(200) NOT NULL,
  code VARCHAR(32) NOT NULL UNIQUE,
  address TEXT,
  timezone VARCHAR(64),
  phone VARCHAR(32),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
  supplier_id BIGSERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  code VARCHAR(64) UNIQUE,
  contact_name VARCHAR(200),
  contact_phone VARCHAR(64),
  contact_email VARCHAR(200),
  address TEXT,
  payment_terms VARCHAR(100),
  preferred BOOLEAN DEFAULT FALSE,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Products master catalogue
CREATE TABLE IF NOT EXISTS products (
  product_id BIGSERIAL PRIMARY KEY,
  sku VARCHAR(64) NOT NULL UNIQUE,
  upc VARCHAR(64),
  name VARCHAR(300) NOT NULL,
  description TEXT,
  brand VARCHAR(128),
  category VARCHAR(128),
  unit VARCHAR(32) NOT NULL,
  unit_size DECIMAL(12,4),
  cost_price NUMERIC(14,4) NOT NULL DEFAULT 0,
  retail_price NUMERIC(14,4) NOT NULL DEFAULT 0,
  reorder_point INTEGER DEFAULT 0,
  reorder_qty INTEGER DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  allow_fractional_qty BOOLEAN DEFAULT FALSE,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Product <> Supplier
CREATE TABLE IF NOT EXISTS product_suppliers (
  product_supplier_id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  supplier_id BIGINT NOT NULL REFERENCES suppliers(supplier_id) ON DELETE CASCADE,
  supplier_sku VARCHAR(128),
  lead_time_days INTEGER,
  cost_price NUMERIC(14,4),
  min_order_qty INTEGER,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(product_id, supplier_id)
);

-- Inventory: per-location stock levels
CREATE TABLE IF NOT EXISTS inventory (
  inventory_id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  location_id BIGINT NOT NULL REFERENCES locations(location_id) ON DELETE CASCADE,
  qty_on_hand NUMERIC(18,4) NOT NULL DEFAULT 0,
  qty_reserved NUMERIC(18,4) NOT NULL DEFAULT 0,
  qty_available NUMERIC(18,4) GENERATED ALWAYS AS (qty_on_hand - qty_reserved) STORED,
  last_cost NUMERIC(14,4),
  last_updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(product_id, location_id)
);

-- Inventory movements (audit)
CREATE TABLE IF NOT EXISTS inventory_movements (
  movement_id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  location_id BIGINT NOT NULL REFERENCES locations(location_id) ON DELETE CASCADE,
  movement_type VARCHAR(50) NOT NULL,
  reference_type VARCHAR(50),
  reference_id BIGINT,
  quantity NUMERIC(18,4) NOT NULL,
  unit_cost NUMERIC(14,4),
  performed_by BIGINT,
  notes TEXT,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Customers / CRM
CREATE TABLE IF NOT EXISTS customers (
  customer_id BIGSERIAL PRIMARY KEY,
  external_customer_uuid UUID UNIQUE,
  name VARCHAR(300) NOT NULL,
  phone VARCHAR(64),
  email VARCHAR(200),
  loyalty_card VARCHAR(64) UNIQUE,
  address TEXT,
  city VARCHAR(128),
  region VARCHAR(128),
  postal_code VARCHAR(32),
  country VARCHAR(64),
  gender VARCHAR(16),
  date_of_birth DATE,
  points_balance NUMERIC(18,4) DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Employees
CREATE TABLE IF NOT EXISTS employees (
  employee_id BIGSERIAL PRIMARY KEY,
  username VARCHAR(128) UNIQUE NOT NULL,
  full_name VARCHAR(200) NOT NULL,
  email VARCHAR(200),
  role VARCHAR(100),
  is_active BOOLEAN DEFAULT TRUE,
  last_login timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Employee logs
CREATE TABLE IF NOT EXISTS employee_logs (
  log_id BIGSERIAL PRIMARY KEY,
  employee_id BIGINT REFERENCES employees(employee_id) ON DELETE SET NULL,
  location_id BIGINT REFERENCES locations(location_id) ON DELETE SET NULL,
  action VARCHAR(150) NOT NULL,
  details JSONB,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Purchase orders
CREATE TABLE IF NOT EXISTS purchase_orders (
  po_id BIGSERIAL PRIMARY KEY,
  po_number VARCHAR(64) NOT NULL UNIQUE,
  supplier_id BIGINT NOT NULL REFERENCES suppliers(supplier_id),
  location_id BIGINT NOT NULL REFERENCES locations(location_id),
  status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
  total_amount NUMERIC(18,4) DEFAULT 0,
  placed_by BIGINT REFERENCES employees(employee_id),
  expected_date DATE,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS purchase_order_lines (
  po_line_id BIGSERIAL PRIMARY KEY,
  po_id BIGINT NOT NULL REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
  product_id BIGINT NOT NULL REFERENCES products(product_id),
  quantity NUMERIC(18,4) NOT NULL,
  unit_cost NUMERIC(14,4),
  received_quantity NUMERIC(18,4) DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(po_id, product_id)
);

-- Sales
CREATE TABLE IF NOT EXISTS sales (
  sale_id BIGSERIAL PRIMARY KEY,
  sale_uuid UUID UNIQUE DEFAULT gen_random_uuid(),
  sale_number VARCHAR(64) NOT NULL UNIQUE,
  location_id BIGINT NOT NULL REFERENCES locations(location_id),
  cashier_id BIGINT REFERENCES employees(employee_id),
  customer_id BIGINT REFERENCES customers(customer_id),
  sale_time timestamptz NOT NULL DEFAULT now(),
  subtotal NUMERIC(18,4) NOT NULL DEFAULT 0,
  discount_total NUMERIC(18,4) DEFAULT 0,
  tax_total NUMERIC(18,4) DEFAULT 0,
  total NUMERIC(18,4) NOT NULL DEFAULT 0,
  payment_method VARCHAR(64),
  payment_details JSONB,
  status VARCHAR(32) DEFAULT 'COMPLETED',
  synced BOOLEAN DEFAULT FALSE,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Sale lines
CREATE TABLE IF NOT EXISTS sale_lines (
  sale_line_id BIGSERIAL PRIMARY KEY,
  sale_id BIGINT NOT NULL REFERENCES sales(sale_id) ON DELETE CASCADE,
  product_id BIGINT NOT NULL REFERENCES products(product_id),
  location_id BIGINT NOT NULL REFERENCES locations(location_id),
  sku_snapshot VARCHAR(64),
  description_snapshot VARCHAR(300),
  quantity NUMERIC(18,4) NOT NULL,
  unit_price NUMERIC(14,4) NOT NULL,
  unit_cost NUMERIC(14,4),
  discount NUMERIC(14,4) DEFAULT 0,
  line_total NUMERIC(18,4) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Payments
CREATE TABLE IF NOT EXISTS payments (
  payment_id BIGSERIAL PRIMARY KEY,
  sale_id BIGINT NOT NULL REFERENCES sales(sale_id) ON DELETE CASCADE,
  amount NUMERIC(18,4) NOT NULL,
  method VARCHAR(64) NOT NULL,
  provider_txn_id VARCHAR(200),
  paid_at timestamptz NOT NULL DEFAULT now()
);

-- Refunds
CREATE TABLE IF NOT EXISTS refunds (
  refund_id BIGSERIAL PRIMARY KEY,
  refund_number VARCHAR(64) UNIQUE,
  sale_id BIGINT REFERENCES sales(sale_id) ON DELETE SET NULL,
  location_id BIGINT REFERENCES locations(location_id),
  processed_by BIGINT REFERENCES employees(employee_id),
  refund_total NUMERIC(18,4) NOT NULL,
  reason TEXT,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS refund_lines (
  refund_line_id BIGSERIAL PRIMARY KEY,
  refund_id BIGINT NOT NULL REFERENCES refunds(refund_id) ON DELETE CASCADE,
  sale_line_id BIGINT REFERENCES sale_lines(sale_line_id),
  product_id BIGINT NOT NULL REFERENCES products(product_id),
  quantity NUMERIC(18,4) NOT NULL,
  unit_price NUMERIC(14,4),
  line_total NUMERIC(18,4) NOT NULL
);

-- Transfers
CREATE TABLE IF NOT EXISTS inventory_transfers (
  transfer_id BIGSERIAL PRIMARY KEY,
  transfer_number VARCHAR(64) UNIQUE,
  from_location_id BIGINT REFERENCES locations(location_id),
  to_location_id BIGINT REFERENCES locations(location_id),
  requested_by BIGINT REFERENCES employees(employee_id),
  status VARCHAR(32) DEFAULT 'REQUESTED',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS inventory_transfer_lines (
  transfer_line_id BIGSERIAL PRIMARY KEY,
  transfer_id BIGINT NOT NULL REFERENCES inventory_transfers(transfer_id) ON DELETE CASCADE,
  product_id BIGINT NOT NULL REFERENCES products(product_id),
  quantity NUMERIC(18,4) NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_upc ON products(upc);
CREATE INDEX IF NOT EXISTS idx_inventory_prod_loc ON inventory(product_id, location_id);
CREATE INDEX IF NOT EXISTS idx_sales_location_time ON sales(location_id, sale_time DESC);
CREATE INDEX IF NOT EXISTS idx_sale_lines_product ON sale_lines(product_id);
CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_product_suppliers_prod ON product_suppliers(product_id);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_employees_username ON employees(username);

-- End of schema
