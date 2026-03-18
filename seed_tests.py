"""
Seed script to populate the database with test data.

This script creates 10 tests with 10 questions each, including multi-language support
for test names, question text, and answer options.

Usage:
    python seed_tests.py
"""

import asyncio
import random
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, init_db
from app.models.level import Level
from app.models.subject import Subject
from app.models.test import Test
from app.models.question import Question
from app.models.question_option import QuestionOption


async def seed_database():
    """Seed the database with test data."""
    
    # Initialize database tables
    await init_db()
    print("✓ Database initialized")
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if subject exists, create if not
            subject = await session.execute(
                __import__('sqlalchemy').select(Subject).limit(1)
            )
            subject = subject.scalars().first()
            
            if not subject:
                subject = Subject(
                    name_en="Mathematics",
                    name_uz="Matematika",
                    name_ru="Математика"
                )
                session.add(subject)
                await session.flush()
                print("✓ Created subject: Mathematics")
            else:
                print(f"✓ Using existing subject: {subject.name_en}")
            
            # Check if level exists, create if not
            level = await session.execute(
                __import__('sqlalchemy').select(Level).where(Level.subject_id == subject.id).limit(1)
            )
            level = level.scalars().first()
            
            if not level:
                level = Level(
                    subject_id=subject.id,
                    name_en="Level 1",
                    name_uz="Daraja 1",
                    name_ru="Уровень 1"
                )
                session.add(level)
                await session.flush()
                print("✓ Created level: Level 1")
            else:
                print(f"✓ Using existing level: {level.name_en}")
            
            # Create 10 tests
            for test_num in range(1, 11):
                test = Test(
                    level_id=level.id,
                    name_en=f"Test {test_num}",
                    name_uz=f"Test {test_num}",
                    name_ru=f"Тест {test_num}",
                    price=Decimal("10.00")
                )
                session.add(test)
                await session.flush()
                
                print(f"\n✓ Created test {test_num}: {test.name_en}")
                
                # Create 10 questions for each test
                for question_num in range(1, 11):
                    correct_answer = random.choice(['A', 'B', 'C', 'D'])
                    
                    question = Question(
                        test_id=test.id,
                        text_en=f"Question {question_num}",
                        text_uz=f"Savol {question_num}",
                        text_ru=f"Вопрос {question_num}",
                        correct_answer=correct_answer
                    )
                    session.add(question)
                    await session.flush()
                    
                    # Create 4 options (A, B, C, D)
                    for option_idx, option_label in enumerate(['A', 'B', 'C', 'D'], 1):
                        option = QuestionOption(
                            question_id=question.id,
                            label=option_label,
                            text_en=f"Option {option_label}",
                            text_uz=f"Variant {option_label}",
                            text_ru=f"Вариант {option_label}"
                        )
                        session.add(option)
                    
                    print(f"  ✓ Created question {question_num} (correct: {correct_answer})")
                
                await session.flush()
            
            # Commit all changes
            await session.commit()
            print("\n✅ Database seeding completed successfully!")
            print("   - 10 tests created")
            print("   - 100 questions created")
            print("   - 400 question options created")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error during seeding: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
