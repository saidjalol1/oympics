"""Migration: create payments table for Click payment integration."""

import asyncio
from app.database import engine
from sqlalchemy import text


async def run():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
                amount DECIMAL(10, 2) NOT NULL,
                click_trans_id INTEGER,
                click_paydoc_id INTEGER,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_payment_user_test ON payments (user_id, test_id)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_payment_status ON payments (status)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_payment_click_trans ON payments (click_trans_id)"
        ))
    print("Migration complete: payments table created.")


if __name__ == "__main__":
    asyncio.run(run())
