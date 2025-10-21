-- Create databases for all services
-- Use DO block to handle IF NOT EXISTS logic for older PostgreSQL versions
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'user_db') THEN
        CREATE DATABASE user_db;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'category_db') THEN
        CREATE DATABASE category_db;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'expense_db') THEN
        CREATE DATABASE expense_db;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'income_db') THEN
        CREATE DATABASE income_db;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'recurring_db') THEN
        CREATE DATABASE recurring_db;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'goals_db') THEN
        CREATE DATABASE goals_db;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'debt_db') THEN
        CREATE DATABASE debt_db;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'account_db') THEN
        CREATE DATABASE account_db;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'subscription_db') THEN
        CREATE DATABASE subscription_db;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'currency_db') THEN
        CREATE DATABASE currency_db;
    END IF;
END
$$;

-- Grant permissions to postgres user
GRANT ALL PRIVILEGES ON DATABASE user_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE category_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE expense_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE income_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE recurring_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE goals_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE debt_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE account_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE subscription_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE currency_db TO postgres;