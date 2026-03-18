"""Database migration to add multi-language support to questions table.

This migration adds translation columns for English, Uzbek, and Russian
to the questions table, enabling multi-language content storage.

Migration: Add translation columns to questions table
- Adds text_en, text_uz, text_ru columns (nullable initially)
- Copies existing text values to text_en
- Sets text_uz and text_ru to same value as text_en
- Makes translation columns non-nullable
- Adds indexes on all three language columns
- Makes original text column nullable for backward compatibility
"""

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """Get the database file path."""
    db_path = Path(__file__).parent.parent.parent / "quiz_auth.db"
    return db_path


def migration_up() -> None:
    """Apply the migration: add translation columns to questions table."""
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if questions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='questions'"
        )
        if not cursor.fetchone():
            print("✓ questions table doesn't exist, nothing to update")
            return
        
        # Check if translation columns already exist
        cursor.execute("PRAGMA table_info(questions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "text_en" in columns:
            print("✓ Translation columns already exist, no update needed")
            return
        
        print("Adding multi-language support to questions table...")
        
        cursor.execute("BEGIN TRANSACTION")
        
        # Step 1: Add translation columns as nullable
        cursor.execute("ALTER TABLE questions ADD COLUMN text_en VARCHAR(1000)")
        cursor.execute("ALTER TABLE questions ADD COLUMN text_uz VARCHAR(1000)")
        cursor.execute("ALTER TABLE questions ADD COLUMN text_ru VARCHAR(1000)")
        print("✓ Added translation columns (text_en, text_uz, text_ru)")
        
        # Step 2: Copy existing text values to text_en
        cursor.execute("UPDATE questions SET text_en = text WHERE text_en IS NULL")
        print("✓ Copied existing text values to text_en")
        
        # Step 3: Set text_uz and text_ru to same value as text_en
        cursor.execute("UPDATE questions SET text_uz = text_en WHERE text_uz IS NULL")
        cursor.execute("UPDATE questions SET text_ru = text_en WHERE text_ru IS NULL")
        print("✓ Set text_uz and text_ru to same value as text_en")
        
        # Step 4: SQLite doesn't support making columns non-nullable directly
        # We need to recreate the table with the new constraints
        
        # Create backup of current data
        cursor.execute("""
            CREATE TABLE questions_backup AS 
            SELECT * FROM questions
        """)
        print("✓ Created backup of existing data")
        
        # Drop the original table
        cursor.execute("DROP TABLE questions")
        print("✓ Dropped original table")
        
        # Create new table with updated schema
        cursor.execute("""
            CREATE TABLE questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                text VARCHAR(1000),
                text_en VARCHAR(1000) NOT NULL,
                text_uz VARCHAR(1000) NOT NULL,
                text_ru VARCHAR(1000) NOT NULL,
                correct_answer VARCHAR(1) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE,
                CONSTRAINT ck_question_correct_answer CHECK (correct_answer IN ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'))
            )
        """)
        print("✓ Created new table with non-nullable translation columns")
        
        # Restore data from backup
        cursor.execute("""
            INSERT INTO questions (id, test_id, text, text_en, text_uz, text_ru, correct_answer, created_at, updated_at)
            SELECT id, test_id, text, text_en, text_uz, text_ru, correct_answer, created_at, updated_at
            FROM questions_backup
        """)
        print("✓ Restored data from backup")
        
        # Create indexes on all three language columns
        cursor.execute("CREATE INDEX idx_question_text_en ON questions(text_en)")
        cursor.execute("CREATE INDEX idx_question_text_uz ON questions(text_uz)")
        cursor.execute("CREATE INDEX idx_question_text_ru ON questions(text_ru)")
        print("✓ Created indexes on translation columns")
        
        # Recreate the test_id index
        cursor.execute("CREATE INDEX idx_question_test_id ON questions(test_id)")
        print("✓ Recreated index on test_id column")
        
        # Recreate the original text index for backward compatibility
        cursor.execute("CREATE INDEX idx_question_text ON questions(text)")
        print("✓ Recreated index on original text column")
        
        # Drop backup table
        cursor.execute("DROP TABLE questions_backup")
        print("✓ Cleaned up backup table")
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(questions)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        if all(col in columns for col in ["text_en", "text_uz", "text_ru"]):
            print("✓ Verified all translation columns exist")
        else:
            raise Exception("Migration verification failed: missing translation columns")
        
        # Verify data integrity
        cursor.execute("SELECT COUNT(*) FROM questions WHERE text_en IS NULL OR text_uz IS NULL OR text_ru IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            raise Exception(f"Migration verification failed: {null_count} rows have NULL translation values")
        
        print("✓ Verified data integrity")
        
        conn.commit()
        print("\n✓ Migration completed successfully")
        print("Questions table now supports multi-language content (EN/UZ/RU)")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        
        # Try to restore from backup if it exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions_backup'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE IF EXISTS questions")
                cursor.execute("ALTER TABLE questions_backup RENAME TO questions")
                conn.commit()
                print("✓ Restored original table from backup")
        except Exception as restore_error:
            print(f"✗ Failed to restore backup: {restore_error}")
        
        raise
    finally:
        conn.close()


def migration_down() -> None:
    """Rollback the migration: remove translation columns from questions table."""
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if questions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='questions'"
        )
        if not cursor.fetchone():
            print("✓ questions table doesn't exist, nothing to rollback")
            return
        
        # Check if translation columns exist
        cursor.execute("PRAGMA table_info(questions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "text_en" not in columns:
            print("✓ Translation columns don't exist, nothing to rollback")
            return
        
        print("Rolling back multi-language support from questions table...")
        
        cursor.execute("BEGIN TRANSACTION")
        
        # Create backup of current data
        cursor.execute("""
            CREATE TABLE questions_backup AS 
            SELECT * FROM questions
        """)
        print("✓ Created backup of current data")
        
        # Drop the current table
        cursor.execute("DROP TABLE questions")
        print("✓ Dropped current table")
        
        # Recreate table with original schema
        cursor.execute("""
            CREATE TABLE questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                text VARCHAR(1000) NOT NULL,
                correct_answer VARCHAR(1) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE,
                CONSTRAINT ck_question_correct_answer CHECK (correct_answer IN ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'))
            )
        """)
        print("✓ Created table with original schema")
        
        # Restore data (copy text_en back to text if text is NULL)
        cursor.execute("""
            INSERT INTO questions (id, test_id, text, correct_answer, created_at, updated_at)
            SELECT id, test_id, COALESCE(text, text_en), correct_answer, created_at, updated_at
            FROM questions_backup
        """)
        print("✓ Restored data (copied text_en to text)")
        
        # Recreate original indexes
        cursor.execute("CREATE INDEX idx_question_test_id ON questions(test_id)")
        cursor.execute("CREATE INDEX idx_question_text ON questions(text)")
        print("✓ Recreated original indexes")
        
        # Drop backup table
        cursor.execute("DROP TABLE questions_backup")
        print("✓ Cleaned up backup table")
        
        # Verify rollback
        cursor.execute("PRAGMA table_info(questions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "text_en" not in columns and "text_uz" not in columns and "text_ru" not in columns:
            print("✓ Verified translation columns removed")
        else:
            raise Exception("Rollback verification failed: translation columns still exist")
        
        # Verify data integrity
        cursor.execute("SELECT COUNT(*) FROM questions WHERE text IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            raise Exception(f"Rollback verification failed: {null_count} rows have NULL text values")
        
        print("✓ Verified data integrity")
        
        conn.commit()
        print("\n✓ Rollback completed successfully")
        print("Questions table restored to original schema")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Rollback failed: {e}")
        
        # Try to restore from backup if it exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions_backup'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE IF EXISTS questions")
                cursor.execute("ALTER TABLE questions_backup RENAME TO questions")
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
