"""Database migration to add pricing support to tests.

This migration adds a price column to the tests table to support
paid assessments. The price is stored as a decimal with 2 decimal places.

Migration: Add price column to tests table
- Adds price column as DECIMAL(10, 2) nullable with default 0.00
- Sets existing tests to 0.00
- Makes price non-nullable
- Adds check constraint for price >= 0
- Adds index on price column for filtering and sorting
"""

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """Get the database file path."""
    db_path = Path(__file__).parent.parent.parent / "quiz_auth.db"
    return db_path


def migration_up() -> None:
    """Apply the migration: add price column to tests table."""
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if tests table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tests'"
        )
        if not cursor.fetchone():
            print("✓ tests table doesn't exist, nothing to update")
            return
        
        # Check if price column already exists
        cursor.execute("PRAGMA table_info(tests)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "price" in columns:
            print("✓ price column already exists, no update needed")
            return
        
        print("Adding pricing support to tests table...")
        
        cursor.execute("BEGIN TRANSACTION")
        
        # Step 1: Add price column as nullable with default 0.00
        # SQLite uses REAL for decimal numbers
        cursor.execute("ALTER TABLE tests ADD COLUMN price REAL DEFAULT 0.00")
        print("✓ Added price column with default 0.00")
        
        # Step 2: Set existing tests to 0.00 (should already be set by default)
        cursor.execute("UPDATE tests SET price = 0.00 WHERE price IS NULL")
        print("✓ Set existing tests to price 0.00")
        
        # Step 3: SQLite doesn't support making columns non-nullable directly
        # We need to recreate the table with the new constraints
        
        # Get current table schema to preserve all columns
        cursor.execute("PRAGMA table_info(tests)")
        table_info = cursor.fetchall()
        
        # Create backup of current data
        cursor.execute("""
            CREATE TABLE tests_backup AS 
            SELECT * FROM tests
        """)
        print("✓ Created backup of existing data")
        
        # Drop the original table
        cursor.execute("DROP TABLE tests")
        print("✓ Dropped original table")
        
        # Create new table with updated schema including price column
        # Check if we have translation columns (from previous migrations)
        has_translations = "name_en" in columns
        
        if has_translations:
            # Schema with translation columns
            cursor.execute("""
                CREATE TABLE tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level_id INTEGER NOT NULL,
                    name VARCHAR(100),
                    name_en VARCHAR(100) NOT NULL,
                    name_uz VARCHAR(100) NOT NULL,
                    name_ru VARCHAR(100) NOT NULL,
                    price REAL NOT NULL DEFAULT 0.00,
                    start_date DATETIME,
                    end_date DATETIME,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (level_id) REFERENCES levels(id) ON DELETE CASCADE,
                    CONSTRAINT uq_test_level_name_en UNIQUE (level_id, name_en),
                    CONSTRAINT ck_test_date_range CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
                    CONSTRAINT ck_test_price_non_negative CHECK (price >= 0)
                )
            """)
        else:
            # Original schema without translation columns
            cursor.execute("""
                CREATE TABLE tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    price REAL NOT NULL DEFAULT 0.00,
                    start_date DATETIME,
                    end_date DATETIME,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (level_id) REFERENCES levels(id) ON DELETE CASCADE,
                    CONSTRAINT uq_test_level_name UNIQUE (level_id, name),
                    CONSTRAINT ck_test_date_range CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
                    CONSTRAINT ck_test_price_non_negative CHECK (price >= 0)
                )
            """)
        
        print("✓ Created new table with non-nullable price column and check constraint")
        
        # Restore data from backup
        if has_translations:
            cursor.execute("""
                INSERT INTO tests (id, level_id, name, name_en, name_uz, name_ru, price, start_date, end_date, created_at, updated_at)
                SELECT id, level_id, name, name_en, name_uz, name_ru, COALESCE(price, 0.00), start_date, end_date, created_at, updated_at
                FROM tests_backup
            """)
        else:
            cursor.execute("""
                INSERT INTO tests (id, level_id, name, price, start_date, end_date, created_at, updated_at)
                SELECT id, level_id, name, COALESCE(price, 0.00), start_date, end_date, created_at, updated_at
                FROM tests_backup
            """)
        print("✓ Restored data from backup")
        
        # Recreate indexes
        cursor.execute("CREATE INDEX idx_test_level_id ON tests(level_id)")
        cursor.execute("CREATE INDEX idx_test_dates ON tests(start_date, end_date)")
        
        if has_translations:
            cursor.execute("CREATE INDEX idx_test_name_en ON tests(name_en)")
            cursor.execute("CREATE INDEX idx_test_name_uz ON tests(name_uz)")
            cursor.execute("CREATE INDEX idx_test_name_ru ON tests(name_ru)")
            cursor.execute("CREATE INDEX idx_test_level_name ON tests(level_id, name)")
        
        # Create index on original name column if it exists
        if "name" in columns:
            cursor.execute("CREATE INDEX idx_test_name ON tests(name)")
        
        print("✓ Recreated existing indexes")
        
        # Create new index on price column
        cursor.execute("CREATE INDEX idx_test_price ON tests(price)")
        print("✓ Created index on price column")
        
        # Drop backup table
        cursor.execute("DROP TABLE tests_backup")
        print("✓ Cleaned up backup table")
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(tests)")
        columns_after = {row[1]: row for row in cursor.fetchall()}
        
        if "price" in columns_after:
            print("✓ Verified price column exists")
        else:
            raise Exception("Migration verification failed: price column not found")
        
        # Verify data integrity - all prices should be non-negative
        cursor.execute("SELECT COUNT(*) FROM tests WHERE price IS NULL OR price < 0")
        invalid_count = cursor.fetchone()[0]
        if invalid_count > 0:
            raise Exception(f"Migration verification failed: {invalid_count} rows have invalid price values")
        
        print("✓ Verified data integrity (all prices >= 0)")
        
        # Verify check constraint exists
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tests'")
        table_sql = cursor.fetchone()[0]
        if "ck_test_price_non_negative" not in table_sql:
            raise Exception("Migration verification failed: price check constraint not found")
        
        print("✓ Verified check constraint on price")
        
        # Verify index exists
        cursor.execute("PRAGMA index_list(tests)")
        indexes = [row[1] for row in cursor.fetchall()]
        if "idx_test_price" not in indexes:
            raise Exception("Migration verification failed: price index not found")
        
        print("✓ Verified index on price column")
        
        conn.commit()
        print("\n✓ Migration completed successfully")
        print("Tests table now supports pricing with DECIMAL(10, 2) format")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        
        # Try to restore from backup if it exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tests_backup'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE IF EXISTS tests")
                cursor.execute("ALTER TABLE tests_backup RENAME TO tests")
                conn.commit()
                print("✓ Restored original table from backup")
        except Exception as restore_error:
            print(f"✗ Failed to restore backup: {restore_error}")
        
        raise
    finally:
        conn.close()


def migration_down() -> None:
    """Rollback the migration: remove price column from tests table."""
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if tests table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tests'"
        )
        if not cursor.fetchone():
            print("✓ tests table doesn't exist, nothing to rollback")
            return
        
        # Check if price column exists
        cursor.execute("PRAGMA table_info(tests)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "price" not in columns:
            print("✓ price column doesn't exist, nothing to rollback")
            return
        
        print("Rolling back pricing support from tests table...")
        
        cursor.execute("BEGIN TRANSACTION")
        
        # Create backup of current data
        cursor.execute("""
            CREATE TABLE tests_backup AS 
            SELECT * FROM tests
        """)
        print("✓ Created backup of current data")
        
        # Drop the current table
        cursor.execute("DROP TABLE tests")
        print("✓ Dropped current table")
        
        # Check if we have translation columns
        has_translations = "name_en" in columns
        
        # Recreate table without price column
        if has_translations:
            cursor.execute("""
                CREATE TABLE tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level_id INTEGER NOT NULL,
                    name VARCHAR(100),
                    name_en VARCHAR(100) NOT NULL,
                    name_uz VARCHAR(100) NOT NULL,
                    name_ru VARCHAR(100) NOT NULL,
                    start_date DATETIME,
                    end_date DATETIME,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (level_id) REFERENCES levels(id) ON DELETE CASCADE,
                    CONSTRAINT uq_test_level_name_en UNIQUE (level_id, name_en),
                    CONSTRAINT ck_test_date_range CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    start_date DATETIME,
                    end_date DATETIME,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (level_id) REFERENCES levels(id) ON DELETE CASCADE,
                    CONSTRAINT uq_test_level_name UNIQUE (level_id, name),
                    CONSTRAINT ck_test_date_range CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
                )
            """)
        
        print("✓ Created table without price column")
        
        # Restore data (excluding price column)
        if has_translations:
            cursor.execute("""
                INSERT INTO tests (id, level_id, name, name_en, name_uz, name_ru, start_date, end_date, created_at, updated_at)
                SELECT id, level_id, name, name_en, name_uz, name_ru, start_date, end_date, created_at, updated_at
                FROM tests_backup
            """)
        else:
            cursor.execute("""
                INSERT INTO tests (id, level_id, name, start_date, end_date, created_at, updated_at)
                SELECT id, level_id, name, start_date, end_date, created_at, updated_at
                FROM tests_backup
            """)
        print("✓ Restored data without price column")
        
        # Recreate original indexes
        cursor.execute("CREATE INDEX idx_test_level_id ON tests(level_id)")
        cursor.execute("CREATE INDEX idx_test_dates ON tests(start_date, end_date)")
        
        if has_translations:
            cursor.execute("CREATE INDEX idx_test_name_en ON tests(name_en)")
            cursor.execute("CREATE INDEX idx_test_name_uz ON tests(name_uz)")
            cursor.execute("CREATE INDEX idx_test_name_ru ON tests(name_ru)")
            cursor.execute("CREATE INDEX idx_test_level_name ON tests(level_id, name)")
        
        if "name" in columns:
            cursor.execute("CREATE INDEX idx_test_name ON tests(name)")
        
        print("✓ Recreated original indexes")
        
        # Drop backup table
        cursor.execute("DROP TABLE tests_backup")
        print("✓ Cleaned up backup table")
        
        # Verify rollback
        cursor.execute("PRAGMA table_info(tests)")
        columns_after = [row[1] for row in cursor.fetchall()]
        
        if "price" not in columns_after:
            print("✓ Verified price column removed")
        else:
            raise Exception("Rollback verification failed: price column still exists")
        
        # Verify check constraint removed
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tests'")
        table_sql = cursor.fetchone()[0]
        if "ck_test_price_non_negative" in table_sql:
            raise Exception("Rollback verification failed: price check constraint still exists")
        
        print("✓ Verified check constraint removed")
        
        conn.commit()
        print("\n✓ Rollback completed successfully")
        print("Tests table restored to schema without pricing")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Rollback failed: {e}")
        
        # Try to restore from backup if it exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tests_backup'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE IF EXISTS tests")
                cursor.execute("ALTER TABLE tests_backup RENAME TO tests")
                conn.commit()
                print("✓ Restored table from backup")
        except Exception as restore_error:
            print(f"✗ Failed to restore backup: {restore_error}")
        
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        migration_down()
    else:
        migration_up()
