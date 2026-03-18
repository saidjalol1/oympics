"""Database migration to add image support to questions.

This migration creates the question_images table for storing
image attachments to questions. Each question can have up to 2 images.

Migration: Create question_images table
- Creates question_images table with columns: id, question_id, image_path, 
  image_order, original_filename, file_size, width, height, created_at
- Adds foreign key constraint from question_id to questions.id with CASCADE delete
- Adds unique constraint on (question_id, image_order)
- Adds check constraint for image_order IN (1, 2)
- Adds check constraint for file_size (0 < size <= 5242880 bytes = 5MB)
- Adds check constraint for width and height (100 <= dimension <= 4000)
- Adds index on question_id for fast lookups
"""

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """Get the database file path."""
    db_path = Path(__file__).parent.parent.parent / "quiz_auth.db"
    return db_path


def migration_up() -> None:
    """Apply the migration: create question_images table."""
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if question_images table already exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='question_images'"
        )
        if cursor.fetchone():
            print("✓ question_images table already exists, no update needed")
            return
        
        # Check if questions table exists (prerequisite)
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='questions'"
        )
        if not cursor.fetchone():
            raise Exception("questions table doesn't exist, cannot create question_images table")
        
        print("Creating question_images table...")
        
        cursor.execute("BEGIN TRANSACTION")
        
        # Create question_images table with all constraints
        cursor.execute("""
            CREATE TABLE question_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                image_path VARCHAR(500) NOT NULL,
                image_order INTEGER NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_size INTEGER NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
                CONSTRAINT uq_question_image_order UNIQUE (question_id, image_order),
                CONSTRAINT ck_question_image_order CHECK (image_order IN (1, 2)),
                CONSTRAINT ck_question_image_file_size CHECK (file_size > 0 AND file_size <= 5242880),
                CONSTRAINT ck_question_image_width CHECK (width >= 100 AND width <= 4000),
                CONSTRAINT ck_question_image_height CHECK (height >= 100 AND height <= 4000)
            )
        """)
        print("✓ Created question_images table with constraints")
        
        # Create index on question_id for fast lookups
        cursor.execute("CREATE INDEX idx_question_image_question_id ON question_images(question_id)")
        print("✓ Created index on question_id")
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(question_images)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        expected_columns = [
            "id", "question_id", "image_path", "image_order", 
            "original_filename", "file_size", "width", "height", "created_at"
        ]
        
        if all(col in columns for col in expected_columns):
            print("✓ Verified all columns exist")
        else:
            missing = [col for col in expected_columns if col not in columns]
            raise Exception(f"Migration verification failed: missing columns {missing}")
        
        # Verify foreign key constraint
        cursor.execute("PRAGMA foreign_key_list(question_images)")
        fk_constraints = cursor.fetchall()
        if not fk_constraints:
            raise Exception("Migration verification failed: foreign key constraint not created")
        print("✓ Verified foreign key constraint")
        
        # Verify indexes
        cursor.execute("PRAGMA index_list(question_images)")
        indexes = [row[1] for row in cursor.fetchall()]
        if "idx_question_image_question_id" not in indexes:
            raise Exception("Migration verification failed: index not created")
        print("✓ Verified index on question_id")
        
        conn.commit()
        print("\n✓ Migration completed successfully")
        print("question_images table created with support for up to 2 images per question")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


def migration_down() -> None:
    """Rollback the migration: drop question_images table."""
    db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if question_images table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='question_images'"
        )
        if not cursor.fetchone():
            print("✓ question_images table doesn't exist, nothing to rollback")
            return
        
        print("Rolling back question_images table...")
        
        cursor.execute("BEGIN TRANSACTION")
        
        # Drop the question_images table
        cursor.execute("DROP TABLE question_images")
        print("✓ Dropped question_images table")
        
        # Verify rollback
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='question_images'"
        )
        if cursor.fetchone():
            raise Exception("Rollback verification failed: question_images table still exists")
        
        print("✓ Verified table removal")
        
        conn.commit()
        print("\n✓ Rollback completed successfully")
        print("question_images table removed")
        
    except Exception as e:
        conn.rollback()
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
