"""
Migration to add type field to categories table
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import text

def upgrade():
    """Add type column to categories table"""
    with engine.connect() as conn:
        # Add type column with default value 'expense'
        conn.execute(text("""
            ALTER TABLE categories 
            ADD COLUMN type VARCHAR(20) NOT NULL DEFAULT 'expense'
        """))
        
        # Create index on type column for better performance
        conn.execute(text("""
            CREATE INDEX idx_categories_type ON categories(type)
        """))
        
        conn.commit()

def downgrade():
    """Remove type column from categories table"""
    with engine.connect() as conn:
        # Drop index first
        conn.execute(text("DROP INDEX IF EXISTS idx_categories_type"))
        
        # Drop type column
        conn.execute(text("ALTER TABLE categories DROP COLUMN type"))
        
        conn.commit()

if __name__ == "__main__":
    upgrade()
    print("Migration completed successfully!")
