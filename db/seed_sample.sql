-- Sample seed data for quick verification

INSERT INTO locations(name, code, address) VALUES ('Main Street Bazaar','MAIN','123 Main St') ON CONFLICT DO NOTHING;
INSERT INTO suppliers(name, code, contact_name) VALUES ('FreshFoods Ltd','FF001','Suresh') ON CONFLICT DO NOTHING;

INSERT INTO products(sku, upc, name, unit, unit_size, cost_price, retail_price)
VALUES ('SKU001','0123456789012','Rice 5kg','bag',5,1200.00,1500.00)
ON CONFLICT (sku) DO NOTHING;

-- insert inventory for product 1 at location 1 if not exists
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM inventory) THEN
    INSERT INTO inventory(product_id, location_id, qty_on_hand, last_cost)
    VALUES (
      (SELECT product_id FROM products WHERE sku='SKU001' LIMIT 1),
      (SELECT location_id FROM locations WHERE code='MAIN' LIMIT 1),
      100,
      1200.00
    );
  END IF;
END$$;

-- sample employee and sale
INSERT INTO employees(username, full_name, email, role) VALUES ('cashier1','Asha Cash','asha@example.com','cashier') ON CONFLICT DO NOTHING;

-- sample customer
INSERT INTO customers(name, phone, email) VALUES ('Raj Kumar','+911234567890','raj@example.com') ON CONFLICT DO NOTHING;
