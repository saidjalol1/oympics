"""Database migration to update question option constraint from A-D to A-J.

This migration updates the check constraint on the question_options table
to allow labels A through J instead of just A through D, enabling support
for more answer choices per question.

Migration: Update ck_question_option_label constraint
- Drops existing constraint if it exists (handles A-D constraint)
- Creates new constraint allowing labels A through J
- Handles SQLite's limitations with constraint modifications
- Includes proper error handling and rollback functionality
"""

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """Get the database file path."""
    # Assuming database is in the project root or configured location
    db_path = Path(__file__).parent.parent.parent / "quiz.db"
    return db_path


def get_constraint_definition(cursor: sqlite3.Cursor, table_name: str, constraint_name: str) -> str:
    """Get the current definition of a constraint from SQLite schema."""
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    result = cursor.fetchone()
    if result and result[0]:
        table_sql = result[0]
        # Look for the constraint in the table definition
        if constraint_name in table_sql:
            return table_sql
    return ""


def constraint_needs_update(cursor: sqlite3.Cursor) -> bool:
    """Check if the constraint needs to be updated from A-D to A-J."""
    table_sql = get_constraint_definition(cursor, "question_options", "ck_question_option_label")
    
    # Check if constraint exists and contains only A-D
    if "ck_question_option_label" in table_sql:
        # If it contains A-J already, no update needed
        if "'I'" in table_sql and "'J'" in table_sql:
            return False
        # If it only contains A-D, update needed
        elif "'A'" in table_sql and "'D'" in table_sql:
            return True
    
    # If no constraint exists, we need to create it
    return True


def migration_up() -> None:
    """Apply the migration: update question option constraint from A-D to A-J."""
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='question_options'"
        )
        if not cursor.fetchone():
            print("✓ question_options table doesn't exist, nothing to update")
            return
        
        # Check if constraint needs updating
        if not constraint_needs_update(cursor):
            print("✓ Constraint already allows A-J labels, no update needed")
            return
        
        print("Updating question option constraint from A-D to A-J...")
        
        # SQLite doesn't support dropping constraints directly
        # We need to recreate the table with the new constraint
        
        # Step 1: Create a backup of the current data
        cursor.execute("BEGIN TRANSACTION")
        
        # Step 2: Get current table structure and data
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='question_options'")
        original_table_sql = cursor.fetchone()[0]
        
        # Step 3: Create temporary table with existing data
        cursor.execute("""
            CREATE TABLE question_options_backup AS 
            SELECT * FROM question_options
        """)
        print("✓ Created backup of existing data")
        
        # Step 4: Drop the original table
        cursor.execute("DROP TABLE question_options")
        print("✓ Dropped original table")
        
        # Step 5: Create new table with updated constraint
        new_table_sql = """
            CREATE TABLE question_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                label VARCHAR(1) NOT NULL,
                text VARCHAR(1000) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_question_option_label UNIQUE (question_id, label),
                CONSTRAINT ck_question_option_label CHECK (label IN ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J')),
                CONSTRAINT fk_question_options_question_id FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
            )
        """
        
        cursor.execute(new_table_sql)
        print("✓ Created new table with A-J constraint")
        
        # Step 6: Restore data from backup
        cursor.execute("""
            INSERT INTO question_options (id, question_id, label, text, created_at, updated_at)
            SELECT id, question_id, label, text, created_at, updated_at
            FROM question_options_backup
        """)
        print("✓ Restored data from backup")
        
        # Step 7: Recreate indexes
        cursor.execute("CREATE INDEX idx_question_option_question_id ON question_options(question_id)")
        cursor.execute("CREATE INDEX idx_question_option_label ON question_options(label)")
        print("✓ Recreated indexes")
        
        # Step 8: Drop backup table
        cursor.execute("DROP TABLE question_options_backup")
        print("✓ Cleaned up backup table")
        
        # Verify the constraint was applied correctly
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='question_options'")
        new_table_def = cursor.fetchone()[0]
        if "'I'" in new_table_def and "'J'" in new_table_def:
            print("✓ Verified constraint now allows A-J labels")
        else:
            raise Exception("Constraint verification failed")
        
        conn.commit()
        print("\n✓ Migration completed successfully")
        print("Question options can now use labels A through J")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        
        # Try to restore from backup if it exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question_options_backup'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE IF EXISTS question_options")
                cursor.execute("ALTER TABLE question_options_backup RENAME TO question_options")
                conn.commit()
                print("✓ Restored original table from backup")
        except Exception as restore_error:
            print(f"✗ Failed to restore backup: {restore_error}")
        
        raise
    finally:
        conn.close()


def migration_down() -> None:
    """Rollback the migration: revert constraint from A-J back to A-D."""
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='question_options'"
        )
        if not cursor.fetchone():
            print("✓ question_options table doesn't exist, nothing to rollback")
            return
        
        # Check if there are any options with labels E-J
        cursor.execute("SELECT COUNT(*) FROM question_options WHERE label IN ('E', 'F', 'G', 'H', 'I', 'J')")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"⚠ Warning: Found {count} question options with labels E-J")
            print("These will be removed during rollback. Continue? (This is a destructive operation)")
            print("Note: In production, you should backup these records first")
        
        print("Rolling back constraint from A-J to A-D...")
        
        cursor.execute("BEGIN TRANSACTION")
        
        # Remove any options with labels E-J
        cursor.execute("DELETE FROM question_options WHERE label IN ('E', 'F', 'G', 'H', 'I', 'J')")
        if count > 0:
            print(f"✓ Removed {count} question options with labels E-J")
        
        # Create backup of current data
        cursor.execute("""
            CREATE TABLE question_options_backup AS 
            SELECT * FROM question_options
        """)
        print("✓ Created backup of remaining data")
        
        # Drop and recreate table with A-D constraint
        cursor.execute("DROP TABLE question_options")
        
        new_table_sql = """
            CREATE TABLE question_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                label VARCHAR(1) NOT NULL,
                text VARCHAR(1000) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_question_option_label UNIQUE (question_id, label),
                CONSTRAINT ck_question_option_label CHECK (label IN ('A', 'B', 'C', 'D')),
                CONSTRAINT fk_question_options_question_id FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
            )
        """
        
        cursor.execute(new_table_sql)
        print("✓ Created new table with A-D constraint")
        
        # Restore remaining data
        cursor.execute("""
            INSERT INTO question_options (id, question_id, label, text, created_at, updated_at)
            SELECT id, question_id, label, text, created_at, updated_at
            FROM question_options_backup
        """)
        print("✓ Restored data from backup")
        
        # Recreate indexes
        cursor.execute("CREATE INDEX idx_question_option_question_id ON question_options(question_id)")
        cursor.execute("CREATE INDEX idx_question_option_label ON question_options(label)")
        print("✓ Recreated indexes")
        
        # Clean up
        cursor.execute("DROP TABLE question_options_backup")
        print("✓ Cleaned up backup table")
        
        conn.commit()
        print("\n✓ Rollback completed successfully")
        print("Question options now restricted to labels A through D")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Rollback failed: {e}")
        
        # Try to restore from backup if it exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question_options_backup'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE IF EXISTS question_options")
                cursor.execute("ALTER TABLE question_options_backup RENAME TO question_options")
                conn.commit()
                print("✓ Restored original table from backup")
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