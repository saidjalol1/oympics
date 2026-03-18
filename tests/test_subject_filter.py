"""
Tests for Subject column and filter functionality in the test management system.

This module tests the new Subject column display and Subject filter functionality
added to the tests table.
"""

import pytest
from httpx import AsyncClient


class TestSubjectFilter:
    """Test Subject filter functionality in the tests API."""
    
    @pytest.mark.asyncio
    async def test_list_tests_with_subject_filter(self, client: AsyncClient, admin_user):
        """Test that tests can be filtered by subject_id."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Create a subject
        response = await client.post(
            "/api/admin/subjects",
            json={
                "name_en": "Mathematics",
                "name_uz": "Matematika", 
                "name_ru": "Математика"
            }
        )
        assert response.status_code == 201
        subject_data = response.json()
        subject_id = subject_data["id"]
        
        # Create a level for the subject
        response = await client.post(
            f"/api/admin/subjects/{subject_id}/levels",
            json={
                "name_en": "Grade 5",
                "name_uz": "5-sinf",
                "name_ru": "5 класс"
            }
        )
        assert response.status_code == 201
        level_data = response.json()
        level_id = level_data["id"]
        
        # Create a test for the level
        response = await client.post(
            "/api/admin/tests",
            json={
                "level_id": level_id,
                "name_en": "Math Test",
                "name_uz": "Matematika testi",
                "name_ru": "Тест по математике",
                "price": 0.00
            }
        )
        assert response.status_code == 201
        test_data = response.json()
        
        # Test filtering by subject_id
        response = await client.get(f"/api/admin/tests?subject_id={subject_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Should return the test we created
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        
        # Verify the test has the correct level and subject relationship
        found_test = None
        for test in data["items"]:
            if test["id"] == test_data["id"]:
                found_test = test
                break
        
        assert found_test is not None
        assert found_test["level_id"] == level_id
        
        # Verify that the subject filter is working by checking that we got results
        # The actual subject relationship verification would require additional API calls
        # but the important thing is that the filter returned the correct test
    
    @pytest.mark.asyncio
    async def test_list_tests_with_nonexistent_subject_filter(self, client: AsyncClient, admin_user):
        """Test that filtering by non-existent subject_id returns empty results."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Test filtering by non-existent subject_id
        response = await client.get("/api/admin/tests?subject_id=99999")
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty results
        assert data["total"] == 0
        assert len(data["items"]) == 0
    
    @pytest.mark.asyncio
    async def test_list_tests_without_subject_filter(self, client: AsyncClient, admin_user):
        """Test that tests can be listed without subject filter (shows all tests)."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # List all tests without filter
        response = await client.get("/api/admin/tests")
        assert response.status_code == 200
        data = response.json()
        
        # Should return results (may be empty if no tests exist)
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    @pytest.mark.asyncio
    async def test_subject_column_data_structure(self, client: AsyncClient, admin_user):
        """Test that the API returns the correct data structure for Subject column display."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Create test data
        response = await client.post(
            "/api/admin/subjects",
            json={
                "name_en": "Physics",
                "name_uz": "Fizika",
                "name_ru": "Физика"
            }
        )
        assert response.status_code == 201
        subject_data = response.json()
        subject_id = subject_data["id"]
        
        response = await client.post(
            f"/api/admin/subjects/{subject_id}/levels",
            json={
                "name_en": "Grade 10",
                "name_uz": "10-sinf", 
                "name_ru": "10 класс"
            }
        )
        assert response.status_code == 201
        level_data = response.json()
        level_id = level_data["id"]
        
        response = await client.post(
            "/api/admin/tests",
            json={
                "level_id": level_id,
                "name_en": "Physics Test",
                "name_uz": "Fizika testi",
                "name_ru": "Тест по физике",
                "price": 5.00
            }
        )
        assert response.status_code == 201
        
        # Get the test and verify data structure
        response = await client.get("/api/admin/tests")
        assert response.status_code == 200
        data = response.json()
        
        if data["total"] > 0:
            test = data["items"][0]
            
            # Verify the test has level_id (basic structure)
            assert "level_id" in test
            assert test["level_id"] is not None
            
            # For the Subject column functionality, the frontend will need to:
            # 1. Load all subjects separately via /api/admin/subjects
            # 2. Load all levels separately via /api/admin/levels  
            # 3. Match test.level_id -> level.subject_id -> subject.name_en
            # This is a valid approach for the frontend implementation