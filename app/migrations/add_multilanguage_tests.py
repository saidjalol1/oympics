"""Database migration to add multi-language support to tests table.

This migration adds translation columns for English, Uzbek, and Russian
to the tests table, enabling multi-language content storage.

Migration: Add translation columns to tests table
- Adds name_en, name_uz, name_ru columns (nullable initially)
- Copies existing name values to name_en
- Sets name_uz and name_ru to same value as name_en
- Makes translation columns non-nullable
- Adds indexes on all three language columns
- Adds unique constraint on (level_id, name_en)
- Makes original name column nullable for backward compatibility
"""

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """Get the database file path."""
    db_path = Path(__file__).parent.parent.parent / "quiz_auth.db"
    return db_path


def migration_up() -> None:
    """Apply the migration: add translation columns to tests table."""
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
        
        # Check if translation columns already exist
        cursor.execute("PRAGMA table_info(tests)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "name_en" in columns:
            print("✓ Translation columns already exist, no update needed")
            return
        
        print("Adding multi-language support to tests table...")
        
        cursor.execute("BEGIN TRANSACTION")
        
        # Step 1: Add translation columns as nullable
        cursor.execute("ALTER TABLE tests ADD COLUMN name_en VARCHAR(100)")
        cursor.execute("ALTER TABLE tests ADD COLUMN name_uz VARCHAR(100)")
        cursor.execute("ALTER TABLE tests ADD COLUMN name_ru VARCHAR(100)")
        print("✓ Added translation columns (name_en, name_uz, name_ru)")
        
        # Step 2: Copy existing name values to name_en
        cursor.execute("UPDATE tests SET name_en = name WHERE name_en IS NULL")
        print("✓ Copied existing name values to name_en")
        
        # Step 3: Set name_uz and name_ru to same value as name_en
        cursor.execute("UPDATE tests SET name_uz = name_en WHERE name_uz IS NULL")
        cursor.execute("UPDATE tests SET name_ru = name_en WHERE name_ru IS NULL")
        print("✓ Set name_uz and name_ru to same value as name_en")
        
        # Step 4: SQLite doesn't support making columns non-nullable directly
        # We need to recreate the table with the new constraints
        
        # Create backup of current data
        cursor.execute("""
            CREATE TABLE tests_backup AS 
            SELECT * FROM tests
        """)
        print("✓ Created backup of existing data")
        
        # Drop the original table
        cursor.execute("DROP TABLE tests")
        print("✓ Dropped original table")
        
        # Create new table with updated schema
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
        print("✓ Created new table with non-nullable translation columns")
        
        # Restore data from backup
        cursor.execute("""
            INSERT INTO tests (id, level_id, name, name_en, name_uz, name_ru, start_date, end_date, created_at, updated_at)
            SELECT id, level_id, name, name_en, name_uz, name_ru, start_date, end_date, created_at, updated_at
            FROM tests_backup
        """)
        print("✓ Restored data from backup")
        
        # Create indexes on all three language columns
        cursor.execute("CREATE INDEX idx_test_name_en ON tests(name_en)")
        cursor.execute("CREATE INDEX idx_test_name_uz ON tests(name_uz)")
        cursor.execute("CREATE INDEX idx_test_name_ru ON tests(name_ru)")
        print("✓ Created indexes on translation columns")
        
        # Recreate the level_id index
        cursor.execute("CREATE INDEX idx_test_level_id ON tests(level_id)")
        print("✓ Recreated index on level_id column")
        
        # Recreate the original name index for backward compatibility
        cursor.execute("CREATE INDEX idx_test_name ON tests(name)")
        print("✓ Recreated index on original name column")
        
        # Recreate the dates index
        cursor.execute("CREATE INDEX idx_test_dates ON tests(start_date, end_date)")
        print("✓ Recreated index on date columns")
        
        # Recreate the composite index
        cursor.execute("CREATE INDEX idx_test_level_name ON tests(level_id, name)")
        print("✓ Recreated composite index on level_id and name")
        
        # Drop backup table
        cursor.execute("DROP TABLE tests_backup")
        print("✓ Cleaned up backup table")
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(tests)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        if all(col in columns for col in ["name_en", "name_uz", "name_ru"]):
            print("✓ Verified all translation columns exist")
        else:
            raise Exception("Migration verification failed: missing translation columns")
        
        # Verify data integrity
        cursor.execute("SELECT COUNT(*) FROM tests WHERE name_en IS NULL OR name_uz IS NULL OR name_ru IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            raise Exception(f"Migration verification failed: {null_count} rows have NULL translation values")
        
        print("✓ Verified data integrity")
        
        conn.commit()
        print("\n✓ Migration completed successfully")
        print("Tests table now supports multi-language content (EN/UZ/RU)")
        
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
    """Rollback the migration: remove translation columns from tests table."""
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
        
        # Check if translation columns exist
        cursor.execute("PRAGMA table_info(tests)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "name_en" not in columns:
            print("✓ Translation columns don't exist, nothing to rollback")
            return
        
        print("Rolling back multi-language support from tests table...")
        
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
        
        # Recreate table with original schema
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
        print("✓ Created table with original schema")
        
        # Restore data (copy name_en back to name if name is NULL)
        cursor.execute("""
            INSERT INTO tests (id, level_id, name, start_date, end_date, created_at, updated_at)
            SELECT id, level_id, COALESCE(name, name_en), start_date, end_date, created_at, updated_at
            FROM tests_backup
        """)
        print("✓ Restored data (copied name_en to name)")
        
        # Recreate original indexes
        cursor.execute("CREATE INDEX idx_test_level_id ON tests(level_id)")
        cursor.execute("CREATE INDEX idx_test_name ON tests(name)")
        cursor.execute("CREATE INDEX idx_test_dates ON tests(start_date, end_date)")
        cursor.execute("CREATE INDEX idx_test_level_name ON tests(level_id, name)")
        print("✓ Recreated original indexes")
        
        # Drop backup table
        cursor.execute("DROP TABLE tests_backup")
        print("✓ Cleaned up backup table")
        
        # Verify rollback
        cursor.execute("PRAGMA table_info(tests)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "name_en" not in columns and "name_uz" not in columns and "name_ru" not in columns:
            print("✓ Verified translation columns removed")
        else:
            raise Exception("Rollback verification failed: translation columns still exist")
        
        # Verify data integrity
        cursor.execute("SELECT COUNT(*) FROM tests WHERE name IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            raise Exception(f"Rollback verification failed: {null_count} rows have NULL name values")
        
        print("✓ Verified data integrity")
        
        conn.commit()
        print("\n✓ Rollback completed successfully")
        print("Tests table restored to original schema")
        
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
