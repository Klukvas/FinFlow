#!/usr/bin/env python3
"""
Database Seed Script — Creates 3 demo users (Free/Pro/Enterprise) with 2 years of data.

Usage:
    python scripts/seed_demo_data.py [--host localhost] [--port 5433] [--clean]

Options:
    --host      PostgreSQL host (default: localhost)
    --port      PostgreSQL port (default: 5433, mapped from Docker)
    --user      PostgreSQL user (default: postgres)
    --password  PostgreSQL password (default: postgres)
    --clean     Delete existing demo data before seeding

Demo credentials (all passwords: Demo1234!):
    Free user:       free@demo.finflow.ltd       (basic plan)
    Pro user:        pro@demo.finflow.ltd        (professional plan)
    Enterprise user: enterprise@demo.finflow.ltd (enterprise plan)
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

DEMO_PASSWORD = "Demo1234!"

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

NOW = datetime.now(timezone.utc)
TWO_YEARS_AGO = NOW - timedelta(days=730)
USER_CREATED_AT = TWO_YEARS_AGO

# ──────────────────────────────────────────────────────────────
# User profiles
# ──────────────────────────────────────────────────────────────

PROFILES = [
    {
        "email": "free@demo.finflow.ltd",
        "plan": "basic",
        "currency": "USD",
        "accounts": [
            ("Cash Wallet", "CASH", "USD", 312.40),
            ("Main Bank Account", "BANK", "USD", 1580.25),
        ],
        "expense_categories": ["Food & Groceries", "Transport", "Housing & Utilities"],
        "income_types": ["salary", "rare_freelance"],
        "expense_freq_multiplier": 0.55,  # ~20 txns/month
        "goals_count": 1,
        "debts_count": 1,
        "recurring_count": 2,
        "monthly_budgets": {},
    },
    {
        "email": "pro@demo.finflow.ltd",
        "plan": "professional",
        "currency": "USD",
        "accounts": [
            ("Cash Wallet", "CASH", "USD", 487.50),
            ("Main Bank Account", "BANK", "USD", 3215.80),
            ("Savings Account", "BANK", "USD", 8450.00),
        ],
        "expense_categories": [
            "Food & Groceries", "Transport", "Housing & Utilities",
            "Entertainment", "Shopping", "Health", "Education",
        ],
        "income_types": ["salary", "freelance", "investments"],
        "expense_freq_multiplier": 1.0,  # ~35 txns/month
        "goals_count": 2,
        "debts_count": 2,
        "recurring_count": 3,
        "monthly_budgets": {
            "Food & Groceries": 600.00,
            "Transport": 200.00,
            "Entertainment": 150.00,
        },
    },
    {
        "email": "enterprise@demo.finflow.ltd",
        "plan": "enterprise",
        "currency": "USD",
        "accounts": [
            ("Cash Wallet", "CASH", "USD", 725.00),
            ("Main Bank Account", "BANK", "USD", 12450.30),
            ("Savings Account", "BANK", "USD", 25000.00),
            ("Credit Card", "CREDIT", "USD", -1280.50),
            ("EUR Account", "BANK", "EUR", 3500.00),
        ],
        "expense_categories": [
            "Food & Groceries", "Transport", "Housing & Utilities",
            "Entertainment", "Shopping", "Health", "Education",
        ],
        "income_types": ["salary", "freelance", "investments", "consulting"],
        "expense_freq_multiplier": 1.4,  # ~50 txns/month
        "goals_count": 3,
        "debts_count": 3,
        "recurring_count": 5,
        "monthly_budgets": {
            "Food & Groceries": 800.00,
            "Transport": 300.00,
            "Housing & Utilities": 1500.00,
            "Entertainment": 200.00,
            "Shopping": 400.00,
            "Health": 200.00,
            "Education": 150.00,
        },
    },
]

# ──────────────────────────────────────────────────────────────
# Expense / Income templates
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
    "Consulting": [
        ("Strategic consulting", 500, 2000),
        ("Technical advisory", 300, 1000),
    ],
}

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def get_conn(db_name: str, host: str, port: int, user: str, password: str):
    return psycopg2.connect(
        dbname=db_name, host=host, port=port, user=user, password=password
    )


def random_date_in_month(year: int, month: int) -> date:
    if month == 12:
        max_day = 31
    else:
        next_month = date(year, month + 1, 1)
        max_day = (next_month - timedelta(days=1)).day
    day = random.randint(1, max_day)
    return date(year, month, day)


def random_datetime_in_month(year: int, month: int) -> datetime:
    d = random_date_in_month(year, month)
    hour = random.randint(8, 22)
    minute = random.randint(0, 59)
    return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=timezone.utc)


def months_in_range():
    """Yield (year, month) tuples for the past 24 months."""
    current = TWO_YEARS_AGO.replace(day=1)
    end = NOW.replace(day=1)
    while current <= end:
        yield current.year, current.month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)


# ──────────────────────────────────────────────────────────────
# Seed steps (per-user)
# ──────────────────────────────────────────────────────────────

def seed_user(conn_params, email: str) -> int:
    conn = get_conn(DATABASES["user"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing = cur.fetchone()
    if existing:
        print(f"  User already exists: id={existing[0]}")
        cur.close()
        conn.close()
        return existing[0]

    hashed_pw = _bcrypt.hashpw(DEMO_PASSWORD.encode(), _bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO users (email, hashed_password, base_currency, role, status, tutorial_version, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (email, hashed_pw, "USD", "user", "active", 1, USER_CREATED_AT),
    )
    user_id = cur.fetchone()[0]
    print(f"  Created user: id={user_id}, email={email}")
    cur.close()
    conn.close()
    return user_id


def seed_workspace(conn_params, user_id: int) -> str:
    # Check if workspace already exists via user's default_workspace_id
    conn = get_conn(DATABASES["user"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT default_workspace_id FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and row[0]:
        print(f"  Workspace already exists: {row[0]}")
        return str(row[0])

    workspace_id = str(uuid.uuid4())

    conn = get_conn(DATABASES["workspace"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(
        """INSERT INTO workspaces (id, name, type, owner_user_id, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (workspace_id, "Personal", "personal", user_id, USER_CREATED_AT, USER_CREATED_AT),
    )
    cur.execute(
        """INSERT INTO workspace_members (workspace_id, user_id, role, status, joined_at, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (workspace_id, user_id, "owner", "active", USER_CREATED_AT, USER_CREATED_AT, USER_CREATED_AT),
    )
    cur.close()
    conn.close()

    conn = get_conn(DATABASES["user"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("UPDATE users SET default_workspace_id = %s WHERE id = %s", (workspace_id, user_id))
    cur.close()
    conn.close()

    print(f"  Created workspace: {workspace_id}")
    return workspace_id


def seed_subscription(conn_params, user_id: int, plan: str):
    conn = get_conn(DATABASES["subscription"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()

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
            str(user_id), plan, "active",
            USER_CREATED_AT, NOW + timedelta(days=30),
            True, USER_CREATED_AT, NOW,
        ),
    )
    print(f"  Created {plan} subscription.")
    cur.close()
    conn.close()


def seed_accounts(conn_params, user_id: int, workspace_id: str, account_defs: list) -> dict:
    conn = get_conn(DATABASES["account"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    account_ids = {}
    for name, acc_type, currency, balance in account_defs:
        cur.execute(
            """INSERT INTO accounts (name, type, currency, balance, is_active, is_archived, owner_id, workspace_id, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (name, acc_type, currency, balance, True, False, user_id, workspace_id, USER_CREATED_AT, USER_CREATED_AT),
        )
        account_ids[name] = cur.fetchone()[0]
        print(f"  Account: {name} ({currency}, balance={balance})")

    cur.close()
    conn.close()
    return account_ids


def seed_categories(conn_params, user_id: int, workspace_id: str,
                    expense_cats: list, monthly_budgets: dict) -> dict:
    conn = get_conn(DATABASES["category"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    all_categories = [(c, "EXPENSE") for c in expense_cats] + [
        ("Salary", "INCOME"),
        ("Freelance", "INCOME"),
        ("Investments", "INCOME"),
        ("Consulting", "INCOME"),
    ]

    cat_ids = {}
    for name, cat_type in all_categories:
        budget = monthly_budgets.get(name)
        cur.execute(
            """INSERT INTO categories (name, user_id, workspace_id, type, monthly_budget, created_by, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (name, user_id, workspace_id, cat_type, budget, "USER", USER_CREATED_AT, USER_CREATED_AT),
        )
        cat_ids[name] = cur.fetchone()[0]

    print(f"  Created {len(cat_ids)} categories")
    cur.close()
    conn.close()
    return cat_ids


def seed_expenses(conn_params, user_id: int, workspace_id: str,
                  category_ids: dict, account_ids: dict, profile: dict):
    conn = get_conn(DATABASES["expense"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    multiplier = profile["expense_freq_multiplier"]
    allowed_cats = profile["expense_categories"]
    account_names = list(account_ids.keys())
    has_eur = any("EUR" in n for n in account_names)
    total = 0

    for year, month in months_in_range():
        month_expenses = []

        for cat_name in allowed_cats:
            templates = EXPENSE_TEMPLATES.get(cat_name)
            if not templates:
                continue
            cat_id = category_ids.get(cat_name)
            if not cat_id:
                continue

            freq_min, freq_max = EXPENSE_FREQUENCY[cat_name]
            count = max(0, round(random.randint(freq_min, freq_max) * multiplier))

            for _ in range(count):
                desc, amt_min, amt_max = random.choice(templates)
                amount = round(random.uniform(amt_min, amt_max), 2)
                expense_date = random_date_in_month(year, month)
                if expense_date > NOW.date():
                    continue

                # Pick account: 30% cash, 70% bank, enterprise gets occasional EUR
                currency = "USD"
                if has_eur and random.random() < 0.15:
                    account_id = account_ids.get("EUR Account", account_ids[account_names[1]])
                    currency = "EUR"
                elif random.random() < 0.3:
                    account_id = account_ids["Cash Wallet"]
                else:
                    account_id = account_ids["Main Bank Account"]

                created_at = datetime(
                    expense_date.year, expense_date.month, expense_date.day,
                    random.randint(8, 22), random.randint(0, 59), 0, tzinfo=timezone.utc,
                )
                month_expenses.append((
                    amount, expense_date, desc, user_id, workspace_id,
                    cat_id, account_id, currency, created_at, created_at,
                ))

        if month_expenses:
            execute_values(
                cur,
                """INSERT INTO expenses (amount, date, description, user_id, workspace_id,
                   category_id, account_id, currency, created_at, updated_at) VALUES %s""",
                month_expenses,
            )
            total += len(month_expenses)

    print(f"  Created {total} expenses across 24 months")
    cur.close()
    conn.close()


def seed_incomes(conn_params, user_id: int, workspace_id: str,
                 category_ids: dict, account_ids: dict, profile: dict):
    conn = get_conn(DATABASES["income"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    income_types = profile["income_types"]
    bank_id = account_ids["Main Bank Account"]
    has_eur = "EUR Account" in account_ids
    total = 0

    for year, month in months_in_range():
        month_incomes = []

        # Salary — always on ~25th
        if "salary" in income_types:
            salary_cat_id = category_ids.get("Salary")
            if salary_cat_id:
                salary_date = date(year, month, min(25, 28))
                if salary_date <= NOW.date():
                    amount = round(random.uniform(4200, 4800), 2)
                    created_at = datetime(salary_date.year, salary_date.month, salary_date.day,
                                          10, 0, 0, tzinfo=timezone.utc)
                    month_incomes.append((
                        user_id, workspace_id, amount, salary_cat_id, bank_id,
                        "USD", "Monthly salary", salary_date, created_at, created_at,
                    ))

        # Freelance
        if "freelance" in income_types:
            freelance_cat_id = category_ids.get("Freelance")
            if freelance_cat_id:
                count = random.randint(0, 3)
                for _ in range(count):
                    desc, amt_min, amt_max = random.choice(INCOME_TEMPLATES["Freelance"])
                    amount = round(random.uniform(amt_min, amt_max), 2)
                    income_date = random_date_in_month(year, month)
                    if income_date > NOW.date():
                        continue
                    created_at = datetime(income_date.year, income_date.month, income_date.day,
                                          random.randint(10, 18), random.randint(0, 59), 0, tzinfo=timezone.utc)
                    month_incomes.append((
                        user_id, workspace_id, amount, freelance_cat_id, bank_id,
                        "USD", desc, income_date, created_at, created_at,
                    ))

        # Rare freelance (for free plan — 1 every ~3 months)
        if "rare_freelance" in income_types:
            freelance_cat_id = category_ids.get("Freelance")
            if freelance_cat_id and random.random() < 0.33:
                desc, amt_min, amt_max = random.choice(INCOME_TEMPLATES["Freelance"])
                amount = round(random.uniform(amt_min, amt_max), 2)
                income_date = random_date_in_month(year, month)
                if income_date <= NOW.date():
                    created_at = datetime(income_date.year, income_date.month, income_date.day,
                                          14, 0, 0, tzinfo=timezone.utc)
                    month_incomes.append((
                        user_id, workspace_id, amount, freelance_cat_id, bank_id,
                        "USD", desc, income_date, created_at, created_at,
                    ))

        # Investments
        if "investments" in income_types:
            investment_cat_id = category_ids.get("Investments")
            if investment_cat_id and random.random() < 0.3:
                desc, amt_min, amt_max = random.choice(INCOME_TEMPLATES["Investments"])
                amount = round(random.uniform(amt_min, amt_max), 2)
                income_date = random_date_in_month(year, month)
                if income_date <= NOW.date():
                    created_at = datetime(income_date.year, income_date.month, income_date.day,
                                          12, 0, 0, tzinfo=timezone.utc)
                    month_incomes.append((
                        user_id, workspace_id, amount, investment_cat_id, bank_id,
                        "USD", desc, income_date, created_at, created_at,
                    ))

        # Consulting (enterprise)
        if "consulting" in income_types:
            consulting_cat_id = category_ids.get("Consulting")
            if consulting_cat_id and random.random() < 0.5:
                desc, amt_min, amt_max = random.choice(INCOME_TEMPLATES["Consulting"])
                amount = round(random.uniform(amt_min, amt_max), 2)
                currency = "EUR" if has_eur and random.random() < 0.3 else "USD"
                target_account = account_ids.get("EUR Account", bank_id) if currency == "EUR" else bank_id
                income_date = random_date_in_month(year, month)
                if income_date <= NOW.date():
                    created_at = datetime(income_date.year, income_date.month, income_date.day,
                                          11, 0, 0, tzinfo=timezone.utc)
                    month_incomes.append((
                        user_id, workspace_id, amount, consulting_cat_id, target_account,
                        currency, desc, income_date, created_at, created_at,
                    ))

        if month_incomes:
            execute_values(
                cur,
                """INSERT INTO incomes (user_id, workspace_id, amount, category_id, account_id,
                   currency, description, date, created_at, updated_at) VALUES %s""",
                month_incomes,
            )
            total += len(month_incomes)

    print(f"  Created {total} incomes across 24 months")
    cur.close()
    conn.close()


# ── Goals ──

GOAL_POOL = [
    {
        "title": "Emergency Fund",
        "description": "Build a 3-month emergency fund",
        "goal_type": "EMERGENCY_FUND",
        "priority": "HIGH",
        "target_amount": 5000.0,
        "current_amount": 3050.0,
        "milestones": [
            ("First $1000", 1000, 1000, True),
            ("Halfway there", 2500, 2500, True),
            ("Almost done", 4000, 3050, False),
            ("Goal complete", 5000, 3050, False),
        ],
    },
    {
        "title": "New Laptop",
        "description": "Save up for a MacBook Pro",
        "goal_type": "SAVINGS",
        "priority": "MEDIUM",
        "target_amount": 2000.0,
        "current_amount": 620.0,
        "milestones": [
            ("First $500", 500, 500, True),
            ("Halfway", 1000, 620, False),
            ("Goal complete", 2000, 620, False),
        ],
    },
    {
        "title": "Vacation Fund",
        "description": "Summer vacation to Europe",
        "goal_type": "SAVINGS",
        "priority": "LOW",
        "target_amount": 3000.0,
        "current_amount": 1200.0,
        "milestones": [
            ("First $500", 500, 500, True),
            ("$1000 saved", 1000, 1000, True),
            ("Halfway", 1500, 1200, False),
            ("Goal complete", 3000, 1200, False),
        ],
    },
]


def seed_goals(conn_params, user_id: int, workspace_id: str, count: int):
    conn = get_conn(DATABASES["goals"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    goals = GOAL_POOL[:count]

    for g in goals:
        started = USER_CREATED_AT + timedelta(days=random.randint(10, 60))
        progress = round(g["current_amount"] / g["target_amount"] * 100, 1)
        cur.execute(
            """INSERT INTO goals (user_id, workspace_id, title, description, goal_type, priority,
               status, target_amount, current_amount, currency, start_date, target_date,
               progress_percentage, is_milestone_based, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (
                user_id, workspace_id, g["title"], g["description"], g["goal_type"],
                g["priority"], "ACTIVE", g["target_amount"], g["current_amount"],
                "USD", started, NOW + timedelta(days=180),
                progress, True, started, NOW,
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
        print(f"  Goal: {g['title']} (${g['current_amount']}/{g['target_amount']})")

    cur.close()
    conn.close()


# ── Debts ──

DEBT_POOL = [
    {
        "contact_name": "Federal Student Aid",
        "contact_email": "support@studentaid.gov",
        "contact_notes": "Student loan servicer",
        "debt_name": "Student Loan",
        "debt_desc": "Federal student loan for education",
        "debt_type": "loan",
        "initial_amount": 10000.0,
        "current_balance": 7600.0,
        "interest_rate": 4.5,
        "minimum_payment": 200.0,
        "monthly_payment": 200.0,
        "due_years": 3,
    },
    {
        "contact_name": "Alex Johnson",
        "contact_email": "alex@example.com",
        "contact_notes": "Friend",
        "debt_name": "Loan from Alex",
        "debt_desc": "Borrowed for emergency car repair",
        "debt_type": "personal",
        "initial_amount": 500.0,
        "current_balance": 200.0,
        "interest_rate": None,
        "minimum_payment": None,
        "monthly_payment": 100.0,
        "due_years": 1,
    },
    {
        "contact_name": "City Credit Union",
        "contact_email": "loans@creditunion.com",
        "contact_notes": "Auto loan provider",
        "debt_name": "Car Loan",
        "debt_desc": "Auto financing for company car",
        "debt_type": "loan",
        "initial_amount": 15000.0,
        "current_balance": 11200.0,
        "interest_rate": 3.9,
        "minimum_payment": 350.0,
        "monthly_payment": 350.0,
        "due_years": 4,
    },
]


def seed_debts(conn_params, user_id: int, workspace_id: str, count: int):
    conn = get_conn(DATABASES["debt"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    debts = DEBT_POOL[:count]

    for d in debts:
        # Create contact
        cur.execute(
            """INSERT INTO contacts (user_id, workspace_id, name, email, notes, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (user_id, workspace_id, d["contact_name"], d["contact_email"],
             d["contact_notes"], USER_CREATED_AT, USER_CREATED_AT),
        )
        contact_id = cur.fetchone()[0]

        start_date = (TWO_YEARS_AGO - timedelta(days=365)).date()
        due_date = (NOW + timedelta(days=365 * d["due_years"])).date()

        if d["interest_rate"] is not None:
            cur.execute(
                """INSERT INTO debts (user_id, workspace_id, contact_id, name, description, debt_type,
                   currency, initial_amount, current_balance, interest_rate, minimum_payment,
                   start_date, due_date, is_active, is_paid_off, created_at, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    user_id, workspace_id, contact_id,
                    d["debt_name"], d["debt_desc"], d["debt_type"],
                    "USD", d["initial_amount"], d["current_balance"],
                    d["interest_rate"], d["minimum_payment"],
                    start_date, due_date,
                    True, False, USER_CREATED_AT, NOW,
                ),
            )
        else:
            cur.execute(
                """INSERT INTO debts (user_id, workspace_id, contact_id, name, description, debt_type,
                   currency, initial_amount, current_balance, start_date, is_active, is_paid_off,
                   created_at, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    user_id, workspace_id, contact_id,
                    d["debt_name"], d["debt_desc"], d["debt_type"],
                    "USD", d["initial_amount"], d["current_balance"],
                    (TWO_YEARS_AGO + timedelta(days=60)).date(),
                    True, False, USER_CREATED_AT + timedelta(days=60), NOW,
                ),
            )
        debt_id = cur.fetchone()[0]

        # Monthly payments
        payment_count = 0
        for year, month in months_in_range():
            pay_date = date(year, month, 15)
            if pay_date > NOW.date():
                continue
            payment_amt = d["monthly_payment"]
            if d["interest_rate"]:
                principal = round(random.uniform(payment_amt * 0.75, payment_amt * 0.90), 2)
                interest = round(payment_amt - principal, 2)
                cur.execute(
                    """INSERT INTO debt_payments (debt_id, user_id, amount, principal_amount, interest_amount,
                       payment_date, description, payment_method, created_at, updated_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (debt_id, user_id, payment_amt, principal, interest, pay_date,
                     "Monthly payment", "bank_transfer",
                     datetime(pay_date.year, pay_date.month, pay_date.day, 10, 0, 0, tzinfo=timezone.utc),
                     datetime(pay_date.year, pay_date.month, pay_date.day, 10, 0, 0, tzinfo=timezone.utc)),
                )
            else:
                cur.execute(
                    """INSERT INTO debt_payments (debt_id, user_id, amount, principal_amount, payment_date,
                       description, payment_method, created_at, updated_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (debt_id, user_id, payment_amt, payment_amt, pay_date,
                     "Repayment", "cash",
                     datetime(pay_date.year, pay_date.month, pay_date.day, 14, 0, 0, tzinfo=timezone.utc),
                     datetime(pay_date.year, pay_date.month, pay_date.day, 14, 0, 0, tzinfo=timezone.utc)),
                )
            payment_count += 1

        print(f"  Debt: {d['debt_name']} (${d['current_balance']}/{d['initial_amount']}) — {payment_count} payments")

    cur.close()
    conn.close()


# ── Recurring ──

RECURRING_POOL = [
    {
        "name": "Rent",
        "description": "Monthly apartment rent",
        "amount": 1200.00,
        "category": "Housing & Utilities",
        "payment_type": "EXPENSE",
        "schedule_config": '{"day_of_month": 1}',
    },
    {
        "name": "Netflix",
        "description": "Streaming subscription",
        "amount": 15.99,
        "category": "Entertainment",
        "payment_type": "EXPENSE",
        "schedule_config": '{"day_of_month": 5}',
    },
    {
        "name": "Monthly Salary",
        "description": "Regular employment salary",
        "amount": 4500.00,
        "category": "Salary",
        "payment_type": "INCOME",
        "schedule_config": '{"day_of_month": 25}',
    },
    {
        "name": "Gym Membership",
        "description": "Monthly gym subscription",
        "amount": 45.00,
        "category": "Health",
        "payment_type": "EXPENSE",
        "schedule_config": '{"day_of_month": 1}',
    },
    {
        "name": "Cloud Hosting",
        "description": "AWS monthly bill",
        "amount": 85.00,
        "category": "Education",
        "payment_type": "EXPENSE",
        "schedule_config": '{"day_of_month": 3}',
    },
]


def seed_recurring(conn_params, user_id: int, workspace_id: str,
                   category_ids: dict, count: int):
    conn = get_conn(DATABASES["recurring"], **conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    items = RECURRING_POOL[:count]
    today = NOW.date()
    next_exec = today.replace(day=1) + timedelta(days=30)

    for item in items:
        cat_id = category_ids.get(item["category"])
        if not cat_id:
            print(f"  Skipping {item['name']}: category not found")
            continue

        rec_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO recurring_payments (id, user_id, workspace_id, name, description,
               amount, currency, category_id, payment_type, schedule_type, schedule_config,
               start_date, status, next_execution, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                rec_id, user_id, workspace_id, item["name"], item["description"],
                item["amount"], "USD", cat_id,
                item["payment_type"], "monthly", item["schedule_config"],
                TWO_YEARS_AGO.date(), "active", next_exec,
                USER_CREATED_AT, NOW,
            ),
        )
        print(f"  Recurring: {item['name']} (${item['amount']}/monthly)")

    cur.close()
    conn.close()


# ──────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────

def seed_user_profile(profile: dict, conn_params: dict):
    email = profile["email"]
    plan = profile["plan"]
    print(f"\n{'─' * 50}")
    print(f"  Seeding: {email} ({plan})")
    print(f"{'─' * 50}")

    print("\n[1/10] User...")
    user_id = seed_user(conn_params, email)

    print("[2/10] Workspace...")
    workspace_id = seed_workspace(conn_params, user_id)

    print(f"[3/10] Subscription ({plan})...")
    seed_subscription(conn_params, user_id, plan)

    print("[4/10] Accounts...")
    account_ids = seed_accounts(conn_params, user_id, workspace_id, profile["accounts"])

    print("[5/10] Categories...")
    category_ids = seed_categories(
        conn_params, user_id, workspace_id,
        profile["expense_categories"], profile["monthly_budgets"],
    )

    print("[6/10] Expenses...")
    seed_expenses(conn_params, user_id, workspace_id, category_ids, account_ids, profile)

    print("[7/10] Incomes...")
    seed_incomes(conn_params, user_id, workspace_id, category_ids, account_ids, profile)

    print(f"[8/10] Goals ({profile['goals_count']})...")
    seed_goals(conn_params, user_id, workspace_id, profile["goals_count"])

    print(f"[9/10] Debts ({profile['debts_count']})...")
    seed_debts(conn_params, user_id, workspace_id, profile["debts_count"])

    print(f"[10/10] Recurring ({profile['recurring_count']})...")
    seed_recurring(conn_params, user_id, workspace_id, category_ids, profile["recurring_count"])

    print(f"\n  Done: {email}")


# ──────────────────────────────────────────────────────────────
# Clean
# ──────────────────────────────────────────────────────────────

def clean_demo_data(conn_params):
    """Remove all data for all 3 demo users."""
    print("\n--- Cleaning existing demo data ---")

    emails = [p["email"] for p in PROFILES]

    for email in emails:
        conn = get_conn(DATABASES["user"], **conn_params)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT id, default_workspace_id FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            print(f"  No user found for {email}, skipping.")
            continue

        user_id, workspace_id = row
        print(f"  Cleaning {email}: id={user_id}")

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
            conn = get_conn(DATABASES[db_key], **conn_params)
            conn.autocommit = True
            cur = conn.cursor()
            for sql, params in queries:
                cur.execute(sql, params)
                print(f"    [{db_key}] {sql.split()[0]}...{sql.split()[2]}: {cur.rowcount} rows")
            cur.close()
            conn.close()

    print("Clean complete.\n")


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

    conn_params = {
        "host": args.host,
        "port": args.port,
        "user": args.user,
        "password": args.password,
    }

    print("=" * 60)
    print("  Accounting App — Demo Data Seeder")
    print("=" * 60)
    print(f"  Host: {args.host}:{args.port}")
    print(f"  Users: {', '.join(p['email'] for p in PROFILES)}")
    print(f"  Date range: {TWO_YEARS_AGO.date()} → {NOW.date()}")
    print("=" * 60)

    if args.clean:
        clean_demo_data(conn_params)

    for profile in PROFILES:
        seed_user_profile(profile, conn_params)

    print("\n" + "=" * 60)
    print("  Seeding complete!")
    print("  Login credentials (password: Demo1234!):")
    for p in PROFILES:
        print(f"    {p['plan']:15s} → {p['email']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
