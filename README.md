
# Tradexa Technologies — Python/Django Multi-DB Concurrency Assignment - Aniket Khomane

## **1. Task Description**

The assignment was to simulate a **distributed system** where three types of data are stored in **separate SQLite databases**, with **simultaneous insertions using threads**.

**Requirements:**

* Three models:

  * **Users** → `users.db`
    Fields: `id`, `name`, `email`
  * **Products** → `products.db`
    Fields: `id`, `name`, `price`
  * **Orders** → `orders.db`
    Fields: `id`, `user_id`, `product_id`, `quantity`
* **No database-level validation** — all validations must be handled in application logic.
* At least **10 simultaneous insertions** for each model using threads.
* A single Django **management command** to:

  1. Validate data
  2. Insert records concurrently
  3. Print results for each table (inserted & skipped rows)

---

## **2. How I Completed the Assignment**

### **Step 1 — Created Django Project**

```bash
django-admin startproject tradexa_assignment
cd tradexa_assignment
```

### **Step 2 — Created App**

```bash
python manage.py startapp multidb
```

### **Step 3 — Configured Multiple Databases**

* Added three SQLite DB configurations in `settings.py` (`users`, `products`, `orders`).
* Created a **custom database router** (`multidb/routers.py`) to route each model to its respective DB.

### **Step 4 — Created Models**

In `multidb/models.py`:

* **AppUser** model → `users.db`
* **Product** model → `products.db`
* **Order** model → `orders.db`
* Allowed `null` & `blank` to handle all validations in Python code.

### **Step 5 — Ran Migrations for Each Database**

```bash
python manage.py makemigrations multidb
python manage.py migrate --database=users    multidb
python manage.py migrate --database=products multidb
python manage.py migrate --database=orders   multidb
python manage.py migrate  # default DB for Django system tables
```

### **Step 6 — Wrote the Management Command**

* File: `multidb/management/commands/run_inserts.py`
* Responsibilities:

  1. Store input data for Users, Products, Orders.
  2. **Validate**:

     * Users → `name` required, valid email, unique email in batch
     * Products → `name` required, price > 0
     * Orders → quantity > 0, valid user\_id & product\_id
  3. Insert valid records **concurrently** using `ThreadPoolExecutor`.
  4. Skip invalid rows and store reasons.
  5. Print a **detailed report** after insertion.

### **Step 7 — Implemented Concurrency**

* Used `ThreadPoolExecutor(max_workers=10)` for parallel insertions.
* Added a **retry-on-lock** decorator to handle SQLite `database is locked` errors.

### **Step 8 — Ran the Command**

```bash
python manage.py run_inserts
```

Output included:

* Number of inserted rows per table
* Number of skipped rows with reasons

---



---

## **3. How to Run the Project**

1. Clone the repository:

```bash
git clone https://github.com/k-aniket-01/tradexa_assignment.git
cd tradexa_assignment
```

2. Create & activate virtual environment:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install django==5.0.6
```

4. Run migrations for each DB:

```bash
python manage.py makemigrations multidb
python manage.py migrate --database=users    multidb
python manage.py migrate --database=products multidb
python manage.py migrate --database=orders   multidb
python manage.py migrate
```

5. Run the insertion command:

```bash
python manage.py run_inserts
```
## **4. Screenshots**
1. Output Terminal:
<img width="1920" height="1080" alt="Screenshot 2025-08-13 153704" src="https://github.com/user-attachments/assets/599cde10-e756-40aa-8e34-8f6c993ec441" />

2. Products.db :
 
<img width="1920" height="1080" alt="Screenshot 2025-08-13 153558" src="https://github.com/user-attachments/assets/0e620763-aef1-4e88-9297-20e159ff9988" />

3. Users.db :
 
<img width="1920" height="1080" alt="Screenshot 2025-08-13 153612" src="https://github.com/user-attachments/assets/644ca4aa-a87a-4adc-890d-361b3203eec0" />

4. Orders.db :
   
<img width="1920" height="1080" alt="Screenshot 2025-08-13 153543" src="https://github.com/user-attachments/assets/e961cdaf-a42e-422d-8de4-0e613927f4c9" />
