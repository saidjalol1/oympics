#!/usr/bin/env python3
"""
Setup script to initialize the database and create an admin user.

This script:
1. Initializes the database
2. Creates an admin user with the specified email and password
3. Sets is_admin=True and is_verified=True
4. Prints success/error messages
"""

import asyncio
import sys
from sqlalchemy.exc import IntegrityError

from app.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.services.password_service import PasswordService


async def create_admin_user():
    """Create an admin user in the database."""
    admin_email = "saidjalol@gmail.com"
    admin_password = "**_StarsInTheSky_**"
    
    try:
        # Initialize database
        print("Initializing database...")
        await init_db()
        print("✓ Database initialized successfully")
        
        # Create password service instance
        password_service = PasswordService()
        
        # Get database session
        async with AsyncSessionLocal() as session:
            # Check if user already exists
            from sqlalchemy import select
            stmt = select(User).where(User.email == admin_email)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✗ Admin user with email '{admin_email}' already exists")
                return False
            
            # Hash the password
            hashed_password = password_service.hash_password(admin_password)
            
            # Create admin user
            admin_user = User(
                email=admin_email,
                hashed_password=hashed_password,
                is_admin=True,
                is_verified=True
            )
            
            # Add to session and commit
            session.add(admin_user)
            await session.commit()
            
            print(f"✓ Admin user created successfully")
            print(f"  Email: {admin_email}")
            print(f"  Admin: True")
            print(f"  Verified: True")
            return True
            
    except IntegrityError as e:
        print(f"✗ Database integrity error: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error creating admin user: {str(e)}")
        return False


async def main():
    """Main entry point."""
    success = await create_admin_user()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
