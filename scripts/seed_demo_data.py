#!/usr/bin/env python3
"""
Database Seed Script — Creates a demo user with a year of realistic platform usage.

Usage:
    python scripts/seed_demo_data.py [--host localhost] [--port 5433] [--clean]

Options:
    --host      PostgreSQL host (default: localhost)
    --port      PostgreSQL port (default: 5433, mapped from Docker)
    --user      PostgreSQL user (default: postgres)
    --password  PostgreSQL password (default: postgres)
    --clean     Delete existing demo data before seeding

Demo credentials:
    Email:    demo@example.com
    Password: Demo1234!
"""

import argparse
import random
import uuid
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal

import bcrypt as _bcrypt
import psycopg2
from psycopg2.extras import execute_values

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "Demo1234!"
DEMO_CURRENCY = "USD"

# Databases (one per service)
DATABASES = {
    "user": "user_db",
    "workspace": "workspace_db",
    "subscription": "subscription_db",
    "account": "account_db",
    "category": "category_db",
    "expense": "expense_db",
    "income": "income_db",
    "goals": "goals_db",
    "debt": "debt_db",
    "recurring": "recurring_db",
}

# Date range: past 12 months
NOW = datetime.now(timezone.utc)
ONE_YEAR_AGO = NOW - timedelta(days=365)
USER_CREATED_AT = ONE_YEAR_AGO

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def get_conn(db_name: str, host: str, port: int, user: str, password: str):
    return psycopg2.connect(
        dbname=db_name, host=host, port=port, user=user, password=password
    )


def random_date_in_month(year: int, month: int) -> date:
    """Return a random date within the given month."""
    if month == 12:
        max_day = 31
    else:
        next_month = date(year, month + 1, 1)
        max_day = (next_month - timedelta(days=1)).day
    day = random.randint(1, max_day)
    return date(year, month, day)


def random_datetime_in_month(year: int, month: int) -> datetime:
    """Return a random datetime within the given month."""
    d = random_date_in_month(year, month)
    hour = random.randint(8, 22)
    minute = random.randint(0, 59)
    return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=timezone.utc)


def months_in_range():
    """Yield (year, month) tuples for the past 12 months."""
    current = ONE_YEAR_AGO.replace(day=1)
    end = NOW.replace(day=1)
    while current <= end:
        # Don't generate data for future dates
        yield current.year, current.month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)


# ──────────────────────────────────────────────────────────────
# Expense generation data
# ──────────────────────────────────────────────────────────────

EXPENSE_TEMPLATES = {
    "Food & Groceries": [
        ("Grocery store", 45, 120),
        ("Coffee shop", 4, 8),
        ("Restaurant dinner", 25, 65),
        ("Fast food", 8, 18),
        ("Bakery", 5, 15),
    ],
    "Transport": [
        ("Gas station", 35, 60),
        ("Uber ride", 8, 25),
        ("Parking", 3, 15),
        ("Car wash", 10, 25),
    ],
    "Housing & Utilities": [
        ("Electricity bill", 80, 150),
        ("Water bill", 30, 60),
        ("Internet", 50, 70),
        ("Phone bill", 35, 55),
    ],
    "Entertainment": [
        ("Movie tickets", 12, 30),
        ("Streaming service", 10, 20),
        ("Concert tickets", 40, 100),
        ("Books", 10, 25),
    ],
    "Shopping": [
        ("Clothing", 30, 100),
        ("Electronics", 20, 200),
        ("Home supplies", 15, 50),
        ("Amazon order", 10, 80),
    ],
    "Health": [
        ("Pharmacy", 10, 40),
        ("Gym membership", 30, 50),
        ("Doctor visit", 50, 150),
    ],
    "Education": [
        ("Online course", 15, 50),
        ("Books & materials", 10, 40),
    ],
}

# How many expenses per category per month (min, max)
EXPENSE_FREQUENCY = {
    "Food & Groceries": (8, 15),
    "Transport": (3, 6),
    "Housing & Utilities": (2, 4),
    "Entertainment": (1, 3),
    "Shopping": (1, 4),
    "Health": (0, 2),
    "Education": (0, 1),
}

INCOME_TEMPLATES = {
    "Salary": [("Monthly salary", 4200, 4800)],
    "Freelance": [
        ("Web development project", 300, 1200),
        ("Design work", 150, 500),
        ("Consulting", 200, 800),
    ],
    "Investments": [
        ("Dividend payment", 20, 100),
        ("Stock sale profit", 50, 300),
    ],
}

# ──────────────────────────────────────────────────────────────
# Clean existing demo data
# ──────────────────────────────────────────────────────────────

def clean_demo_data(host, port, db_user, db_password):
    """Remove all data associated with the demo user."""
    print("\n--- Cleaning existing demo data ---")

    # 1. Find user ID
    conn = get_conn(DATABASES["user"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT id, default_workspace_id FROM users WHERE email = %s", (DEMO_EMAIL,))
    row = cur.fetchone()
    if not row:
        print("No demo user found, nothing to clean.")
        cur.close()
        conn.close()
        return
    user_id, workspace_id = row
    print(f"Found demo user: id={user_id}, workspace_id={workspace_id}")
    cur.close()
    conn.close()

    # 2. Clean each service database
    cleanup_queries = {
        "expense": [("DELETE FROM expenses WHERE user_id = %s", (user_id,))],
        "income": [("DELETE FROM incomes WHERE user_id = %s", (user_id,))],
        "category": [("DELETE FROM categories WHERE user_id = %s", (user_id,))],
        "account": [("DELETE FROM accounts WHERE owner_id = %s", (user_id,))],
        "goals": [
            ("DELETE FROM milestones WHERE goal_id IN (SELECT id FROM goals WHERE user_id = %s)", (user_id,)),
            ("DELETE FROM goals WHERE user_id = %s", (user_id,)),
        ],
        "debt": [
            ("DELETE FROM debt_payments WHERE user_id = %s", (user_id,)),
            ("DELETE FROM debts WHERE user_id = %s", (user_id,)),
            ("DELETE FROM contacts WHERE user_id = %s", (user_id,)),
        ],
        "recurring": [
            ("DELETE FROM payment_schedules WHERE recurring_payment_id IN (SELECT id FROM recurring_payments WHERE user_id = %s)", (user_id,)),
            ("DELETE FROM recurring_payments WHERE user_id = %s", (user_id,)),
        ],
        "subscription": [
            ("DELETE FROM subscription_consent_log WHERE user_id = %s", (str(user_id),)),
            ("DELETE FROM subscriptions WHERE user_id = %s", (str(user_id),)),
        ],
        "workspace": [
            ("DELETE FROM workspace_invites WHERE workspace_id IN (SELECT id FROM workspaces WHERE owner_user_id = %s)", (user_id,)),
            ("DELETE FROM workspace_members WHERE user_id = %s", (user_id,)),
            ("DELETE FROM workspaces WHERE owner_user_id = %s", (user_id,)),
        ],
        "user": [("DELETE FROM users WHERE id = %s", (user_id,))],
    }

    for db_key, queries in cleanup_queries.items():
        conn = get_conn(DATABASES[db_key], host, port, db_user, db_password)
        conn.autocommit = True
        cur = conn.cursor()
        for sql, params in queries:
            cur.execute(sql, params)
            print(f"  [{db_key}] {sql.split()[0]}...{sql.split()[2]}: {cur.rowcount} rows")
        cur.close()
        conn.close()

    print("Clean complete.\n")


# ──────────────────────────────────────────────────────────────
# Seed functions
# ──────────────────────────────────────────────────────────────

def seed_user(host, port, db_user, db_password) -> int:
    """Create demo user. Returns user ID."""
    print("\n[1/10] Seeding user...")
    conn = get_conn(DATABASES["user"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()

    # Check if user already exists
    cur.execute("SELECT id FROM users WHERE email = %s", (DEMO_EMAIL,))
    existing = cur.fetchone()
    if existing:
        print(f"  User already exists with id={existing[0]}")
        cur.close()
        conn.close()
        return existing[0]

    hashed_pw = _bcrypt.hashpw(DEMO_PASSWORD.encode(), _bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO users (email, hashed_password, base_currency, role, status, tutorial_version, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (DEMO_EMAIL, hashed_pw, DEMO_CURRENCY, "user", "active", 1, USER_CREATED_AT),
    )
    user_id = cur.fetchone()[0]
    print(f"  Created user: id={user_id}, email={DEMO_EMAIL}")
    cur.close()
    conn.close()
    return user_id


def seed_workspace(host, port, db_user, db_password, user_id: int) -> str:
    """Create personal workspace. Returns workspace UUID string."""
    print("\n[2/10] Seeding workspace...")
    workspace_id = str(uuid.uuid4())

    conn = get_conn(DATABASES["workspace"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(
        """INSERT INTO workspaces (id, name, type, owner_user_id, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (workspace_id, "Personal", "PERSONAL", user_id, USER_CREATED_AT, USER_CREATED_AT),
    )
    cur.execute(
        """INSERT INTO workspace_members (workspace_id, user_id, role, status, joined_at, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (workspace_id, user_id, "OWNER", "ACTIVE", USER_CREATED_AT, USER_CREATED_AT, USER_CREATED_AT),
    )
    cur.close()
    conn.close()

    # Update user's default_workspace_id
    conn = get_conn(DATABASES["user"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("UPDATE users SET default_workspace_id = %s WHERE id = %s", (workspace_id, user_id))
    cur.close()
    conn.close()

    print(f"  Created workspace: {workspace_id}")
    return workspace_id


def seed_subscription(host, port, db_user, db_password, user_id: int):
    """Create basic subscription."""
    print("\n[3/10] Seeding subscription...")
    conn = get_conn(DATABASES["subscription"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()

    # Check if subscription exists
    cur.execute("SELECT id FROM subscriptions WHERE user_id = %s", (str(user_id),))
    if cur.fetchone():
        print("  Subscription already exists, skipping.")
        cur.close()
        conn.close()
        return

    cur.execute(
        """INSERT INTO subscriptions (user_id, plan_code, status, started_at, expires_at, auto_renew, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            str(user_id), "professional", "active",
            USER_CREATED_AT, NOW + timedelta(days=30),
            True, USER_CREATED_AT, NOW,
        ),
    )
    print("  Created professional subscription.")
    cur.close()
    conn.close()


def seed_accounts(host, port, db_user, db_password, user_id: int, workspace_id: str) -> dict:
    """Create 2 accounts. Returns {name: id} mapping."""
    print("\n[4/10] Seeding accounts...")
    conn = get_conn(DATABASES["account"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()

    accounts = [
        ("Cash Wallet", "CASH", 487.50),
        ("Main Bank Account", "BANK", 3215.80),
    ]
    account_ids = {}
    for name, acc_type, balance in accounts:
        cur.execute(
            """INSERT INTO accounts (name, type, currency, balance, is_active, is_archived, owner_id, workspace_id, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (name, acc_type, DEMO_CURRENCY, balance, True, False, user_id, workspace_id, USER_CREATED_AT, USER_CREATED_AT),
        )
        account_ids[name] = cur.fetchone()[0]
        print(f"  Created account: {name} (id={account_ids[name]}, balance=${balance})")

    cur.close()
    conn.close()
    return account_ids


def seed_categories(host, port, db_user, db_password, user_id: int, workspace_id: str) -> dict:
    """Create 10 categories. Returns {name: id} mapping."""
    print("\n[5/10] Seeding categories...")
    conn = get_conn(DATABASES["category"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()

    categories = [
        ("Food & Groceries", "EXPENSE"),
        ("Transport", "EXPENSE"),
        ("Housing & Utilities", "EXPENSE"),
        ("Entertainment", "EXPENSE"),
        ("Shopping", "EXPENSE"),
        ("Health", "EXPENSE"),
        ("Education", "EXPENSE"),
        ("Salary", "INCOME"),
        ("Freelance", "INCOME"),
        ("Investments", "INCOME"),
    ]
    cat_ids = {}
    for name, cat_type in categories:
        cur.execute(
            """INSERT INTO categories (name, user_id, workspace_id, type, created_by, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (name, user_id, workspace_id, cat_type, "USER", USER_CREATED_AT, USER_CREATED_AT),
        )
        cat_ids[name] = cur.fetchone()[0]

    print(f"  Created {len(cat_ids)} categories: {list(cat_ids.keys())}")
    cur.close()
    conn.close()
    return cat_ids


def seed_expenses(host, port, db_user, db_password, user_id: int, workspace_id: str,
                  category_ids: dict, account_ids: dict):
    """Generate ~30-45 expenses per month for 12 months."""
    print("\n[6/10] Seeding expenses...")
    conn = get_conn(DATABASES["expense"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()

    cash_id = account_ids["Cash Wallet"]
    bank_id = account_ids["Main Bank Account"]
    total = 0

    for year, month in months_in_range():
        month_expenses = []
        month_count = 0

        for cat_name, templates in EXPENSE_TEMPLATES.items():
            cat_id = category_ids.get(cat_name)
            if not cat_id:
                continue

            freq_min, freq_max = EXPENSE_FREQUENCY[cat_name]
            count = random.randint(freq_min, freq_max)

            for _ in range(count):
                if month_count >= 48:  # Stay under 50/month limit
                    break
                desc, amt_min, amt_max = random.choice(templates)
                amount = round(random.uniform(amt_min, amt_max), 2)
                expense_date = random_date_in_month(year, month)
                # Don't create future expenses
                if expense_date > NOW.date():
                    continue
                account_id = cash_id if random.random() < 0.3 else bank_id
                created_at = datetime(expense_date.year, expense_date.month, expense_date.day,
                                      random.randint(8, 22), random.randint(0, 59), 0, tzinfo=timezone.utc)

                month_expenses.append((
                    amount, expense_date, desc, user_id, workspace_id,
                    cat_id, account_id, DEMO_CURRENCY, created_at, created_at
                ))
                month_count += 1

            if month_count >= 48:
                break

        if month_expenses:
            execute_values(
                cur,
                """INSERT INTO expenses (amount, date, description, user_id, workspace_id,
                   category_id, account_id, currency, created_at, updated_at) VALUES %s""",
                month_expenses,
            )
            total += len(month_expenses)

    print(f"  Created {total} expenses across 12 months.")
    cur.close()
    conn.close()


def seed_incomes(host, port, db_user, db_password, user_id: int, workspace_id: str,
                 category_ids: dict, account_ids: dict):
    """Generate incomes for 12 months."""
    print("\n[7/10] Seeding incomes...")
    conn = get_conn(DATABASES["income"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()

    bank_id = account_ids["Main Bank Account"]
    total = 0

    for year, month in months_in_range():
        month_incomes = []

        # Monthly salary (always on ~25th of the month)
        salary_cat_id = category_ids.get("Salary")
        if salary_cat_id:
            salary_day = min(25, 28)
            salary_date = date(year, month, salary_day)
            if salary_date <= NOW.date():
                amount = round(random.uniform(4200, 4800), 2)
                created_at = datetime(salary_date.year, salary_date.month, salary_date.day,
                                      10, 0, 0, tzinfo=timezone.utc)
                month_incomes.append((
                    user_id, workspace_id, amount, salary_cat_id, bank_id,
                    DEMO_CURRENCY, "Monthly salary", created_at, created_at, created_at
                ))

        # Occasional freelance (0-3 per month)
        freelance_cat_id = category_ids.get("Freelance")
        if freelance_cat_id:
            freelance_count = random.randint(0, 3)
            for _ in range(freelance_count):
                templates = INCOME_TEMPLATES["Freelance"]
                desc, amt_min, amt_max = random.choice(templates)
                amount = round(random.uniform(amt_min, amt_max), 2)
                income_date = random_date_in_month(year, month)
                if income_date > NOW.date():
                    continue
                created_at = datetime(income_date.year, income_date.month, income_date.day,
                                      random.randint(10, 18), random.randint(0, 59), 0, tzinfo=timezone.utc)
                month_incomes.append((
                    user_id, workspace_id, amount, freelance_cat_id, bank_id,
                    DEMO_CURRENCY, desc, created_at, created_at, created_at
                ))

        # Rare investment returns (0-1 per month, ~30% chance)
        investment_cat_id = category_ids.get("Investments")
        if investment_cat_id and random.random() < 0.3:
            templates = INCOME_TEMPLATES["Investments"]
            desc, amt_min, amt_max = random.choice(templates)
            amount = round(random.uniform(amt_min, amt_max), 2)
            income_date = random_date_in_month(year, month)
            if income_date <= NOW.date():
                created_at = datetime(income_date.year, income_date.month, income_date.day,
                                      12, 0, 0, tzinfo=timezone.utc)
                month_incomes.append((
                    user_id, workspace_id, amount, investment_cat_id, bank_id,
                    DEMO_CURRENCY, desc, created_at, created_at, created_at
                ))

        if month_incomes:
            execute_values(
                cur,
                """INSERT INTO incomes (user_id, workspace_id, amount, category_id, account_id,
                   currency, description, date, created_at, updated_at) VALUES %s""",
                month_incomes,
            )
            total += len(month_incomes)

    print(f"  Created {total} incomes across 12 months.")
    cur.close()
    conn.close()


def seed_goals(host, port, db_user, db_password, user_id: int, workspace_id: str):
    """Create 2 goals with milestones."""
    print("\n[8/10] Seeding goals...")
    conn = get_conn(DATABASES["goals"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()

    goals = [
        {
            "title": "Emergency Fund",
            "description": "Build a 3-month emergency fund for unexpected expenses",
            "goal_type": "EMERGENCY_FUND",
            "priority": "HIGH",
            "status": "ACTIVE",
            "target_amount": 5000.0,
            "current_amount": 3050.0,
            "progress_percentage": 61.0,
            "target_date": NOW + timedelta(days=180),
            "milestones": [
                ("First $1000", 1000, 1000, True),
                ("Halfway there", 2500, 2500, True),
                ("Almost done", 4000, 3050, False),
                ("Goal complete", 5000, 3050, False),
            ],
        },
        {
            "title": "New Laptop",
            "description": "Save up for a MacBook Pro for development work",
            "goal_type": "SAVINGS",
            "priority": "MEDIUM",
            "status": "ACTIVE",
            "target_amount": 2000.0,
            "current_amount": 620.0,
            "progress_percentage": 31.0,
            "target_date": NOW + timedelta(days=120),
            "milestones": [
                ("First $500", 500, 500, True),
                ("Halfway", 1000, 620, False),
                ("Goal complete", 2000, 620, False),
            ],
        },
    ]

    for g in goals:
        started = USER_CREATED_AT + timedelta(days=random.randint(10, 60))
        cur.execute(
            """INSERT INTO goals (user_id, workspace_id, title, description, goal_type, priority,
               status, target_amount, current_amount, currency, start_date, target_date,
               progress_percentage, is_milestone_based, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (
                user_id, workspace_id, g["title"], g["description"], g["goal_type"],
                g["priority"], g["status"], g["target_amount"], g["current_amount"],
                DEMO_CURRENCY, started, g["target_date"],
                g["progress_percentage"], True, started, NOW,
            ),
        )
        goal_id = cur.fetchone()[0]

        for idx, (m_title, m_target, m_current, m_done) in enumerate(g["milestones"]):
            completed_at = (started + timedelta(days=random.randint(30, 200))) if m_done else None
            cur.execute(
                """INSERT INTO milestones (goal_id, title, target_amount, current_amount,
                   is_completed, completed_at, order_index, created_at, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (goal_id, m_title, m_target, m_current, m_done, completed_at, idx, started, NOW),
            )

        print(f"  Created goal: {g['title']} (${g['current_amount']}/{g['target_amount']})")

    cur.close()
    conn.close()


def seed_debts(host, port, db_user, db_password, user_id: int, workspace_id: str):
    """Create 2 debts with contacts and payments."""
    print("\n[9/10] Seeding debts...")
    conn = get_conn(DATABASES["debt"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()

    # Create contacts
    cur.execute(
        """INSERT INTO contacts (user_id, workspace_id, name, email, notes, created_at, updated_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (user_id, workspace_id, "Federal Student Aid", "support@studentaid.gov",
         "Student loan servicer", USER_CREATED_AT, USER_CREATED_AT),
    )
    contact_1_id = cur.fetchone()[0]

    cur.execute(
        """INSERT INTO contacts (user_id, workspace_id, name, email, notes, created_at, updated_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (user_id, workspace_id, "Alex Johnson", "alex@example.com",
         "Friend", USER_CREATED_AT, USER_CREATED_AT),
    )
    contact_2_id = cur.fetchone()[0]

    # Debt 1: Student Loan
    cur.execute(
        """INSERT INTO debts (user_id, workspace_id, contact_id, name, description, debt_type,
           currency, initial_amount, current_balance, interest_rate, minimum_payment,
           start_date, due_date, is_active, is_paid_off, created_at, updated_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (
            user_id, workspace_id, contact_1_id,
            "Student Loan", "Federal student loan for education", "loan",
            DEMO_CURRENCY, 10000.0, 7600.0, 4.5, 200.0,
            (ONE_YEAR_AGO - timedelta(days=365)).date(),  # Started 2 years ago
            (NOW + timedelta(days=365 * 3)).date(),  # Due in 3 years
            True, False, USER_CREATED_AT, NOW,
        ),
    )
    debt_1_id = cur.fetchone()[0]

    # Payments for student loan (monthly $200 over the past year)
    payment_count = 0
    for year, month in months_in_range():
        pay_date = date(year, month, 15)
        if pay_date > NOW.date():
            continue
        principal = round(random.uniform(160, 180), 2)
        interest = round(200.0 - principal, 2)
        created_at = datetime(pay_date.year, pay_date.month, pay_date.day, 10, 0, 0, tzinfo=timezone.utc)
        cur.execute(
            """INSERT INTO debt_payments (debt_id, user_id, amount, principal_amount, interest_amount,
               payment_date, description, payment_method, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (debt_1_id, user_id, 200.0, principal, interest, pay_date,
             "Monthly payment", "bank_transfer", created_at, created_at),
        )
        payment_count += 1

    print(f"  Created debt: Student Loan ($10,000 → $7,600) with {payment_count} payments")

    # Debt 2: Friend loan
    cur.execute(
        """INSERT INTO debts (user_id, workspace_id, contact_id, name, description, debt_type,
           currency, initial_amount, current_balance, start_date, is_active, is_paid_off,
           created_at, updated_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (
            user_id, workspace_id, contact_2_id,
            "Loan from Alex", "Borrowed for emergency car repair", "personal",
            DEMO_CURRENCY, 500.0, 200.0,
            (ONE_YEAR_AGO + timedelta(days=60)).date(),
            True, False, USER_CREATED_AT + timedelta(days=60), NOW,
        ),
    )
    debt_2_id = cur.fetchone()[0]

    # 3 payments for friend loan
    for i, amount in enumerate([100, 100, 100]):
        pay_date = (ONE_YEAR_AGO + timedelta(days=90 + i * 60)).date()
        if pay_date > NOW.date():
            continue
        created_at = datetime(pay_date.year, pay_date.month, pay_date.day, 14, 0, 0, tzinfo=timezone.utc)
        cur.execute(
            """INSERT INTO debt_payments (debt_id, user_id, amount, principal_amount, payment_date,
               description, payment_method, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (debt_2_id, user_id, amount, amount, pay_date,
             "Repayment to Alex", "cash", created_at, created_at),
        )

    print(f"  Created debt: Loan from Alex ($500 → $200)")
    cur.close()
    conn.close()


def seed_recurring(host, port, db_user, db_password, user_id: int, workspace_id: str,
                   category_ids: dict):
    """Create 3 recurring payments."""
    print("\n[10/10] Seeding recurring payments...")
    conn = get_conn(DATABASES["recurring"], host, port, db_user, db_password)
    conn.autocommit = True
    cur = conn.cursor()

    housing_cat = category_ids.get("Housing & Utilities")
    entertainment_cat = category_ids.get("Entertainment")
    salary_cat = category_ids.get("Salary")

    recurring_items = [
        {
            "name": "Rent",
            "description": "Monthly apartment rent",
            "amount": 1200.00,
            "category_id": housing_cat,
            "payment_type": "EXPENSE",
            "schedule_type": "monthly",
            "schedule_config": '{"day_of_month": 1}',
        },
        {
            "name": "Netflix",
            "description": "Streaming subscription",
            "amount": 15.99,
            "category_id": entertainment_cat,
            "payment_type": "EXPENSE",
            "schedule_type": "monthly",
            "schedule_config": '{"day_of_month": 5}',
        },
        {
            "name": "Monthly Salary",
            "description": "Regular employment salary",
            "amount": 4500.00,
            "category_id": salary_cat,
            "payment_type": "INCOME",
            "schedule_type": "monthly",
            "schedule_config": '{"day_of_month": 25}',
        },
    ]

    for item in recurring_items:
        if not item["category_id"]:
            print(f"  Skipping {item['name']}: category not found")
            continue

        rec_id = str(uuid.uuid4())
        # Calculate next execution date
        today = NOW.date()
        next_exec = today.replace(day=1) + timedelta(days=30)

        cur.execute(
            """INSERT INTO recurring_payments (id, user_id, workspace_id, name, description,
               amount, currency, category_id, payment_type, schedule_type, schedule_config,
               start_date, status, next_execution, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                rec_id, user_id, workspace_id, item["name"], item["description"],
                item["amount"], DEMO_CURRENCY, item["category_id"],
                item["payment_type"], item["schedule_type"], item["schedule_config"],
                ONE_YEAR_AGO.date(), "active", next_exec,
                USER_CREATED_AT, NOW,
            ),
        )
        print(f"  Created recurring: {item['name']} (${item['amount']}/{item['schedule_type']})")

    cur.close()
    conn.close()


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Seed demo data for accounting app")
    parser.add_argument("--host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=5433, help="PostgreSQL port")
    parser.add_argument("--user", default="postgres", help="PostgreSQL user")
    parser.add_argument("--password", default="postgres", help="PostgreSQL password")
    parser.add_argument("--clean", action="store_true", help="Clean existing demo data first")
    args = parser.parse_args()

    print("=" * 60)
    print("  Accounting App — Demo Data Seeder")
    print("=" * 60)
    print(f"  Host: {args.host}:{args.port}")
    print(f"  Demo user: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print(f"  Date range: {ONE_YEAR_AGO.date()} → {NOW.date()}")
    print("=" * 60)

    if args.clean:
        clean_demo_data(args.host, args.port, args.user, args.password)

    # Seed in dependency order
    user_id = seed_user(args.host, args.port, args.user, args.password)
    workspace_id = seed_workspace(args.host, args.port, args.user, args.password, user_id)
    seed_subscription(args.host, args.port, args.user, args.password, user_id)
    account_ids = seed_accounts(args.host, args.port, args.user, args.password, user_id, workspace_id)
    category_ids = seed_categories(args.host, args.port, args.user, args.password, user_id, workspace_id)
    seed_expenses(args.host, args.port, args.user, args.password, user_id, workspace_id, category_ids, account_ids)
    seed_incomes(args.host, args.port, args.user, args.password, user_id, workspace_id, category_ids, account_ids)
    seed_goals(args.host, args.port, args.user, args.password, user_id, workspace_id)
    seed_debts(args.host, args.port, args.user, args.password, user_id, workspace_id)
    seed_recurring(args.host, args.port, args.user, args.password, user_id, workspace_id, category_ids)

    print("\n" + "=" * 60)
    print("  Seeding complete!")
    print(f"  Login with: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print("=" * 60)


if __name__ == "__main__":
    main()
