"""Tests for JWT authentication module."""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
import jwt
import time


class TestVerifyJwtToken:
    """Tests for verify_jwt_token function."""

    def test_missing_token_returns_401(self):
        """Test that missing Authorization header returns 401."""
        from auth import verify_jwt_token
        
        # Simulate no credentials
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(None)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error_code"] == "UNAUTHORIZED"
        assert "Authentication required" in exc_info.value.detail["message"]

    @patch("auth.get_jwk_client")
    def test_expired_token_returns_401(self, mock_get_client):
        """Test that expired JWT returns 401 with TOKEN_EXPIRED code."""
        from auth import verify_jwt_token
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired.token.here")
        
        mock_client = Mock()
        mock_signing_key = Mock()
        mock_signing_key.key = "test-key"
        mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_get_client.return_value = mock_client
        
        with patch("jwt.decode") as mock_decode:
            mock_decode.side_effect = jwt.exceptions.ExpiredSignatureError("Token expired")
            
            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token(credentials)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail["error_code"] == "TOKEN_EXPIRED"

    @patch("auth.get_jwk_client")
    def test_invalid_token_returns_401(self, mock_get_client):
        """Test that invalid JWT returns 401 with INVALID_TOKEN code."""
        from auth import verify_jwt_token
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.here")
        
        mock_client = Mock()
        mock_signing_key = Mock()
        mock_signing_key.key = "test-key"
        mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_get_client.return_value = mock_client
        
        with patch("jwt.decode") as mock_decode:
            mock_decode.side_effect = jwt.exceptions.InvalidTokenError("Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token(credentials)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail["error_code"] == "INVALID_TOKEN"

    @patch("auth.get_jwk_client")
    def test_valid_token_returns_user_info(self, mock_get_client):
        """Test that valid JWT returns user info."""
        from auth import verify_jwt_token
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token.here")
        
        mock_client = Mock()
        mock_signing_key = Mock()
        mock_signing_key.key = "test-key"
        mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_get_client.return_value = mock_client
        
        expected_payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = expected_payload
            
            result = verify_jwt_token(credentials)
            
            assert result["user_id"] == "user-123"
            assert result["email"] == "test@example.com"


class TestProtectedEndpoints:
    """Tests for protected API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        with patch.dict("os.environ", {"BETTER_AUTH_URL": "http://localhost:3000"}):
            from app import app
            return TestClient(app)

    def test_chat_without_token_returns_401(self, client):
        """Test that POST /chat without token returns 401."""
        response = client.post(
            "/chat",
            json={"query": "What is inverse kinematics?"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"

    def test_chat_stream_without_token_returns_401(self, client):
        """Test that POST /chat/stream without token returns 401."""
        response = client.post(
            "/chat/stream",
            json={"query": "What is a robot?"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"

    def test_history_without_token_returns_401(self, client):
        """Test that GET /history/{session_id} without token returns 401."""
        import uuid
        session_id = str(uuid.uuid4())
        response = client.get(f"/history/{session_id}")
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"

    def test_health_without_token_returns_200(self, client):
        """Test that GET /health is accessible without token."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unavailable"]


class TestGetCurrentUser:
    """Tests for get_current_user function."""

    def test_returns_authenticated_user(self):
        """Test that get_current_user returns AuthenticatedUser."""
        from auth import get_current_user
        from models.auth import AuthenticatedUser
        
        user_info = {"user_id": "user-456", "email": "user@example.com"}
        result = get_current_user(user_info)
        
        assert isinstance(result, AuthenticatedUser)
        assert result.user_id == "user-456"
        assert result.email == "user@example.com"
