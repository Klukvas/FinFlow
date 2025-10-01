-- Create databases for all services
CREATE DATABASE user_db;
CREATE DATABASE category_db;
CREATE DATABASE expense_db;
CREATE DATABASE income_db;
CREATE DATABASE recurring_db;
CREATE DATABASE goals_db;
CREATE DATABASE debt_db;
CREATE DATABASE account_db;

-- Grant permissions to postgres user
GRANT ALL PRIVILEGES ON DATABASE user_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE category_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE expense_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE income_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE recurring_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE goals_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE debt_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE account_db TO postgres;