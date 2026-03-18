"""Database migration to add is_admin column to users table.

This migration adds the is_admin column to support admin role-based access control
for the admin panel user management feature.

Migration: Add is_admin column and indexes to users table
- Adds is_admin BOOLEAN DEFAULT FALSE NOT NULL column
- Creates index on is_admin for authorization checks
- Creates composite index on (is_verified, created_at) for common queries
"""

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """Get the database file path."""
    # Assuming database is in the project root or configured location
    db_path = Path(__file__).parent.parent.parent / "quiz.db"
    return db_path


def migration_up() -> None:
    """Apply the migration: add is_admin column and indexes."""
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if is_admin column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "is_admin" not in columns:
            # Add is_admin column with default FALSE
            cursor.execute(
                "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL"
            )
            print("✓ Added is_admin column to users table")
        else:
            print("✓ is_admin column already exists")
        
        # Create index on is_admin for authorization checks
        try:
            cursor.execute("CREATE INDEX idx_users_admin ON users(is_admin)")
            print("✓ Created index on is_admin column")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print("✓ Index on is_admin already exists")
            else:
                raise
        
        # Create composite index on (is_verified, created_at) for common queries
        try:
            cursor.execute(
                "CREATE INDEX idx_users_verified_created ON users(is_verified, created_at)"
            )
            print("✓ Created composite index on (is_verified, created_at)")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print("✓ Composite index on (is_verified, created_at) already exists")
            else:
                raise
        
        conn.commit()
        print("\n✓ Migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


def migration_down() -> None:
    """Rollback the migration: remove is_admin column and indexes."""
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support dropping columns directly, so we need to recreate the table
        # This is a simplified approach - in production, use Alembic or similar
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "is_admin" in columns:
            print("Note: SQLite doesn't support dropping columns directly.")
            print("To fully rollback, you would need to recreate the table.")
            print("For now, the is_admin column will remain in the database.")
        else:
            print("✓ is_admin column doesn't exist, nothing to rollback")
        
    except Exception as e:
        print(f"\n✗ Rollback failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        migration_down()
    else:
        migration_up()
