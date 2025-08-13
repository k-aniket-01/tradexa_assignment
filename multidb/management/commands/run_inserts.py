import re
import time
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import OperationalError
from multidb.models import AppUser, Product, Order

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def retry_on_lock(fn):
    """Retry decorator for SQLite locked DB errors."""
    def wrapper(*args, **kwargs):
        delay = 0.1
        for _ in range(5):
            try:
                return fn(*args, **kwargs)
            except OperationalError as e:
                if 'locked' in str(e).lower():
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
        raise
    return wrapper


class Command(BaseCommand):
    help = 'Insert sample data concurrently into three databases with validation and report.'

    def handle(self, *args, **options):
        # -------------------- Input Data --------------------
        users_rows = [
            {'id': 1, 'name': 'Alice',   'email': 'alice@example.com'},
            {'id': 2, 'name': 'Bob',     'email': 'bob@example.com'},
            {'id': 3, 'name': 'Charlie', 'email': 'charlie@example.com'},
            {'id': 4, 'name': 'David',   'email': 'david@example.com'},
            {'id': 5, 'name': 'Eve',     'email': 'eve@example.com'},
            {'id': 6, 'name': 'Frank',   'email': 'frank@example.com'},
            {'id': 7, 'name': 'Grace',   'email': 'grace@example.com'},
            {'id': 8, 'name': 'Alice',   'email': 'alice@example.com'},  # duplicate email
            {'id': 9, 'name': 'Henry',   'email': 'henry@example.com'},
            {'id': 10, 'name': '',       'email': 'jane@example.com'},   # missing name
        ]

        products_rows = [
            {'id': 1, 'name': 'Laptop',       'price': '1000.00'},
            {'id': 2, 'name': 'Smartphone',   'price': '700.00'},
            {'id': 3, 'name': 'Headphones',   'price': '150.00'},
            {'id': 4, 'name': 'Monitor',      'price': '300.00'},
            {'id': 5, 'name': 'Keyboard',     'price': '50.00'},
            {'id': 6, 'name': 'Mouse',        'price': '30.00'},
            {'id': 7, 'name': 'Laptop',       'price': '1000.00'},  # duplicate name OK
            {'id': 8, 'name': 'Smartwatch',   'price': '250.00'},
            {'id': 9, 'name': 'Gaming Chair', 'price': '500.00'},
            {'id': 10, 'name': 'Earbuds',     'price': '-50.00'},   # invalid (negative)
        ]

        orders_rows = [
            {'id': 1,  'user_id': 1,  'product_id': 1,  'quantity': 2},
            {'id': 2,  'user_id': 2,  'product_id': 2,  'quantity': 1},
            {'id': 3,  'user_id': 3,  'product_id': 3,  'quantity': 5},
            {'id': 4,  'user_id': 4,  'product_id': 4,  'quantity': 1},
            {'id': 5,  'user_id': 5,  'product_id': 5,  'quantity': 3},
            {'id': 6,  'user_id': 6,  'product_id': 6,  'quantity': 4},
            {'id': 7,  'user_id': 7,  'product_id': 7,  'quantity': 2},
            {'id': 8,  'user_id': 8,  'product_id': 8,  'quantity': 0},    # invalid qty
            {'id': 9,  'user_id': 9,  'product_id': 1,  'quantity': -1},   # invalid qty
            {'id': 10, 'user_id': 10, 'product_id': 11, 'quantity': 2},    # invalid refs
        ]

        # -------------------- Validation --------------------
        seen_emails = set()
        valid_users, skipped_users = [], []
        for u in users_rows:
            reasons = []
            if not u['name']:
                reasons.append("missing name")
            if not EMAIL_RE.match(u['email']):
                reasons.append("invalid email")
            if u['email'] in seen_emails:
                reasons.append("duplicate email")
            if reasons:
                skipped_users.append((u, reasons))
            else:
                seen_emails.add(u['email'])
                valid_users.append(u)

        valid_products, skipped_products = [], []
        for p in products_rows:
            reasons = []
            if not p['name']:
                reasons.append("missing name")
            if Decimal(p['price']) <= 0:
                reasons.append("price must be > 0")
            if reasons:
                skipped_products.append((p, reasons))
            else:
                valid_products.append(p)

        valid_user_ids = {u['id'] for u in valid_users}
        valid_product_ids = {p['id'] for p in valid_products}

        valid_orders, skipped_orders = [], []
        for o in orders_rows:
            reasons = []
            if o['quantity'] <= 0:
                reasons.append("quantity must be > 0")
            if o['user_id'] not in valid_user_ids:
                reasons.append(f"user_id {o['user_id']} not found")
            if o['product_id'] not in valid_product_ids:
                reasons.append(f"product_id {o['product_id']} not found")
            if reasons:
                skipped_orders.append((o, reasons))
            else:
                valid_orders.append(o)

        # -------------------- Insert Functions --------------------
        @retry_on_lock
        def insert_user(row):
            with transaction.atomic(using='users'):
                AppUser.objects.using('users').create(**row)

        @retry_on_lock
        def insert_product(row):
            with transaction.atomic(using='products'):
                Product.objects.using('products').create(**row)

        @retry_on_lock
        def insert_order(row):
            with transaction.atomic(using='orders'):
                Order.objects.using('orders').create(**row)

        # -------------------- Concurrent Inserts --------------------
        with ThreadPoolExecutor(max_workers=10) as ex:
            for _ in as_completed([ex.submit(insert_user, r) for r in valid_users]):
                pass

        with ThreadPoolExecutor(max_workers=10) as ex:
            for _ in as_completed([ex.submit(insert_product, r) for r in valid_products]):
                pass

        with ThreadPoolExecutor(max_workers=10) as ex:
            for _ in as_completed([ex.submit(insert_order, r) for r in valid_orders]):
                pass

        # -------------------- Report --------------------
        self.stdout.write("\n================ RESULTS ================\n")

        self.stdout.write("--- Users Table (users.db) ---")
        self.stdout.write(f"Inserted: {len(valid_users)}")
        self.stdout.write(f"Skipped: {len(skipped_users)}")
        for row, reasons in skipped_users:
            self.stdout.write(f"  id={row['id']} -> {', '.join(reasons)}")

        self.stdout.write("\n--- Products Table (products.db) ---")
        self.stdout.write(f"Inserted: {len(valid_products)}")
        self.stdout.write(f"Skipped: {len(skipped_products)}")
        for row, reasons in skipped_products:
            self.stdout.write(f"  id={row['id']} -> {', '.join(reasons)}")

        self.stdout.write("\n--- Orders Table (orders.db) ---")
        self.stdout.write(f"Inserted: {len(valid_orders)}")
        self.stdout.write(f"Skipped: {len(skipped_orders)}")
        for row, reasons in skipped_orders:
            self.stdout.write(f"  id={row['id']} -> {', '.join(reasons)}")

        self.stdout.write("\n========================================\n")
