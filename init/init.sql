-- Create databases for all services
-- Use individual CREATE DATABASE statements with error handling
CREATE DATABASE user_db;
CREATE DATABASE category_db;
CREATE DATABASE expense_db;
CREATE DATABASE income_db;
CREATE DATABASE recurring_db;
CREATE DATABASE goals_db;
CREATE DATABASE debt_db;
CREATE DATABASE account_db;
CREATE DATABASE subscription_db;
CREATE DATABASE payment_db;
CREATE DATABASE scheduler_db;
CREATE DATABASE currency_db;
CREATE DATABASE workspace_db;
CREATE DATABASE bank_sync_db;
CREATE DATABASE pdf_parser_db;

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
GRANT ALL PRIVILEGES ON DATABASE payment_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE scheduler_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE currency_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE workspace_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE bank_sync_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE pdf_parser_db TO postgres;