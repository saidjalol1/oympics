"""Integration tests for admin panel user management."""

import pytest
from httpx import AsyncClient


class TestAdminPanelAccess:
    """Test admin panel access and authentication."""
    
    @pytest.mark.asyncio
    async def test_admin_can_access_admin_panel(self, client: AsyncClient, admin_user):
        """Test that admin users can access the admin panel."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Access admin panel
        response = await client.get("/admin")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_regular_user_cannot_access_admin_panel(self, client: AsyncClient, regular_user):
        """Test that regular users cannot access the admin panel."""
        # Login as regular user
        response = await client.post(
            "/api/auth/login",
            json={"email": "user@example.com", "password": "userpass123"}
        )
        assert response.status_code == 200
        
        # Try to access admin panel
        response = await client.get("/admin")
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_unauthenticated_user_cannot_access_admin_panel(self, client: AsyncClient):
        """Test that unauthenticated users cannot access the admin panel."""
        response = await client.get("/admin")
        assert response.status_code == 401


class TestUserListEndpoint:
    """Test user list retrieval endpoint."""
    
    @pytest.mark.asyncio
    async def test_admin_can_list_users(self, client: AsyncClient, admin_user):
        """Test that admin can retrieve user list."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Get user list
        response = await client.get("/api/admin/users")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert isinstance(data["users"], list)
        assert data["total"] >= 1  # At least the admin user
    
    @pytest.mark.asyncio
    async def test_regular_user_cannot_list_users(self, client: AsyncClient, regular_user):
        """Test that regular users cannot list users."""
        # Login as regular user
        response = await client.post(
            "/api/auth/login",
            json={"email": "user@example.com", "password": "userpass123"}
        )
        assert response.status_code == 200
        
        # Try to get user list
        response = await client.get("/api/admin/users")
        assert response.status_code == 403


class TestUserCreation:
    """Test user creation endpoint."""
    
    @pytest.mark.asyncio
    async def test_admin_can_create_user(self, client: AsyncClient, admin_user):
        """Test that admin can create a new user."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Create new user
        response = await client.post(
            "/api/admin/users",
            json={
                "email": "newuser@example.com",
                "password": "newpass123",
                "is_verified": True,
                "is_admin": False
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User created successfully"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["is_verified"] is True
        assert data["user"]["is_admin"] is False
        assert "hashed_password" not in data["user"]
    
    @pytest.mark.asyncio
    async def test_cannot_create_user_with_duplicate_email(self, client: AsyncClient, admin_user):
        """Test that duplicate emails are rejected."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Try to create user with existing email
        response = await client.post(
            "/api/admin/users",
            json={
                "email": "admin@example.com",
                "password": "newpass123",
                "is_verified": False,
                "is_admin": False
            }
        )
        assert response.status_code == 409
        data = response.json()
        assert "Email already exists" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_cannot_create_user_with_invalid_email(self, client: AsyncClient, admin_user):
        """Test that invalid emails are rejected."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Try to create user with invalid email
        response = await client.post(
            "/api/admin/users",
            json={
                "email": "invalid-email",
                "password": "newpass123",
                "is_verified": False,
                "is_admin": False
            }
        )
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_cannot_create_user_with_short_password(self, client: AsyncClient, admin_user):
        """Test that short passwords are rejected."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Try to create user with short password
        response = await client.post(
            "/api/admin/users",
            json={
                "email": "newuser@example.com",
                "password": "short",
                "is_verified": False,
                "is_admin": False
            }
        )
        assert response.status_code == 422  # Validation error


class TestUserUpdate:
    """Test user update endpoint."""
    
    @pytest.mark.asyncio
    async def test_admin_can_update_user(self, client: AsyncClient, admin_user, regular_user):
        """Test that admin can update a user."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Update user
        response = await client.put(
            f"/api/admin/users/{regular_user.id}",
            json={
                "email": "updated@example.com",
                "is_verified": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User updated successfully"
        assert data["user"]["email"] == "updated@example.com"
        assert data["user"]["is_verified"] is False
    
    @pytest.mark.asyncio
    async def test_cannot_update_user_with_duplicate_email(self, client: AsyncClient, admin_user, regular_user):
        """Test that duplicate emails are rejected on update."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Try to update user with admin's email
        response = await client.put(
            f"/api/admin/users/{regular_user.id}",
            json={"email": "admin@example.com"}
        )
        assert response.status_code == 409
    
    @pytest.mark.asyncio
    async def test_cannot_update_nonexistent_user(self, client: AsyncClient, admin_user):
        """Test that updating nonexistent user returns 404."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Try to update nonexistent user
        response = await client.put(
            "/api/admin/users/99999",
            json={"email": "updated@example.com"}
        )
        assert response.status_code == 404


class TestUserDeletion:
    """Test user deletion endpoint."""
    
    @pytest.mark.asyncio
    async def test_admin_can_delete_user(self, client: AsyncClient, admin_user, regular_user):
        """Test that admin can delete a user."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Delete user
        response = await client.delete(f"/api/admin/users/{regular_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User deleted successfully"
        
        # Verify user is deleted
        response = await client.get(f"/api/admin/users/{regular_user.id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_admin_cannot_delete_self(self, client: AsyncClient, admin_user):
        """Test that admin cannot delete their own account."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Try to delete self
        response = await client.delete(f"/api/admin/users/{admin_user.id}")
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_cannot_delete_nonexistent_user(self, client: AsyncClient, admin_user):
        """Test that deleting nonexistent user returns 404."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Try to delete nonexistent user
        response = await client.delete("/api/admin/users/99999")
        assert response.status_code == 404


class TestVerificationToggle:
    """Test verification status toggle endpoint."""
    
    @pytest.mark.asyncio
    async def test_admin_can_toggle_verification(self, client: AsyncClient, admin_user, regular_user):
        """Test that admin can toggle verification status."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Toggle verification
        response = await client.patch(f"/api/admin/users/{regular_user.id}/verify")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Verification status toggled successfully"
        assert data["user"]["is_verified"] is False  # Was True, now False
        
        # Toggle again
        response = await client.patch(f"/api/admin/users/{regular_user.id}/verify")
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_verified"] is True  # Back to True
    
    @pytest.mark.asyncio
    async def test_cannot_toggle_verification_for_nonexistent_user(self, client: AsyncClient, admin_user):
        """Test that toggling verification for nonexistent user returns 404."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Try to toggle verification for nonexistent user
        response = await client.patch("/api/admin/users/99999/verify")
        assert response.status_code == 404


class TestSearchAndFilter:
    """Test search and filter functionality."""
    
    @pytest.mark.asyncio
    async def test_search_users_by_email(self, client: AsyncClient, admin_user):
        """Test searching users by email."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Create a test user
        response = await client.post(
            "/api/admin/users",
            json={
                "email": "testuser@example.com",
                "password": "testpass123",
                "is_verified": True,
                "is_admin": False
            }
        )
        assert response.status_code == 201
        
        # Search for user
        response = await client.get("/api/admin/users?search=testuser")
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 1
        assert data["users"][0]["email"] == "testuser@example.com"
    
    @pytest.mark.asyncio
    async def test_filter_users_by_verification_status(self, client: AsyncClient, admin_user, regular_user):
        """Test filtering users by verification status."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Create unverified user
        response = await client.post(
            "/api/admin/users",
            json={
                "email": "unverified@example.com",
                "password": "testpass123",
                "is_verified": False,
                "is_admin": False
            }
        )
        assert response.status_code == 201
        
        # Filter for verified users
        response = await client.get("/api/admin/users?verified_only=true")
        assert response.status_code == 200
        data = response.json()
        for user in data["users"]:
            assert user["is_verified"] is True
        
        # Filter for unverified users
        response = await client.get("/api/admin/users?verified_only=false")
        assert response.status_code == 200
        data = response.json()
        for user in data["users"]:
            assert user["is_verified"] is False


class TestPagination:
    """Test pagination functionality."""
    
    @pytest.mark.asyncio
    async def test_pagination_with_skip_and_limit(self, client: AsyncClient, admin_user):
        """Test pagination with skip and limit parameters."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Create multiple users
        for i in range(5):
            response = await client.post(
                "/api/admin/users",
                json={
                    "email": f"user{i}@example.com",
                    "password": "testpass123",
                    "is_verified": True,
                    "is_admin": False
                }
            )
            assert response.status_code == 201
        
        # Get first page
        response = await client.get("/api/admin/users?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2
        assert data["total"] >= 6  # At least admin + 5 created users
        
        # Get second page
        response = await client.get("/api/admin/users?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2
        assert data["skip"] == 2
    
    @pytest.mark.asyncio
    async def test_invalid_pagination_parameters(self, client: AsyncClient, admin_user):
        """Test that invalid pagination parameters are rejected."""
        # Login as admin
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "adminpass123"}
        )
        assert response.status_code == 200
        
        # Try with negative skip
        response = await client.get("/api/admin/users?skip=-1")
        assert response.status_code == 422
        
        # Try with limit > 100
        response = await client.get("/api/admin/users?limit=101")
        assert response.status_code == 422
        
        # Try with limit = 0
        response = await client.get("/api/admin/users?limit=0")
        assert response.status_code == 422
