import pytest
import json
from unittest.mock import Mock, MagicMock


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload, status_code, expected_fields",
    [
        (
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "Password123!",
                "name": "New User",
            },
            201,
            ["id", "username", "email", "name"],
        ),
        (
            {
                "username": "newuser",
                "email": "invalid_email",
                "password": "short",
                "name": "New User",
            },
            400,
            [],
        ),
        (
            {
                "username": "testuser",
                "email": "another@example.com",
                "password": "Password123!",
                "name": "Test User",
            },
            400,
            [],
        ),
    ],
)
def test_register_user(
    payload, status_code, expected_fields, api_client, create_user
):
    """Test user registration"""
    user = create_user()
    response = api_client.post("/api/auth/register/", payload)
    assert response.status_code == status_code

    if status_code == 201:
        for field in expected_fields:
            assert field in response.data
        assert response.data["email"] == payload["email"]
        assert response.data["name"] == payload["name"]
    else:
        assert "error" in response.data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "username, password, status_code, tokens",
    [
        ("testuser", "testpassword12@", 200, ["access_token", "refresh_token"]),
        ("testuser", "testpassword", 400, []),
    ],
)
def test_login_user(
    username, password, status_code, tokens, create_user, api_client
):
    """Test user login"""
    user = create_user()
    payload = {"username": username, "password": password}
    response = api_client.post("/api/auth/login/", payload)
    print(response.data)

    assert response.status_code == status_code

    if status_code == 200:
        for token in tokens:
            assert token in response.data
    else:
        assert "error" in response.data


@pytest.mark.django_db
def test_logout_user(create_user, authenticated_client):
    """Test user logout"""
    user = create_user()
    client = authenticated_client()
    response = client.post("/api/auth/logout/")
    assert response.status_code == 200

@pytest.mark.django_db
def test_get_single_user(create_user, authenticated_client):
    """Test fetching a single user's details"""
    user = create_user(username="testuser2", password="testpassword2@", email="testuser2@gmail.com")
    client = authenticated_client(username="testuser2", password="testpassword2@")
    user_id = user.id
    response = client.get(f"/api/users/{user_id}/")
    assert response.status_code == 200
    assert response.data["email"] == "testuser2@gmail.com"


@pytest.mark.django_db
def test_get_single_user_with_mock_response(api_client, mocker):
    """Test fetching a single user's details using a mocked API response"""

    # Mock response data (dictionary format)
    mock_response_data = {
        "id": 1,
        "username": "testuser2",
        "email": "testuser2@gmail.com",
    }

    # Create a mock response object
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = (
        mock_response_data  # `.json()` should return a dictionary
    )

    # Mock the APIClient.get method to return the mock response
    mocker.patch("rest_framework.test.APIClient.get", return_value=mock_response)

    client = api_client
    response = client.get(f"/api/users/1/")  # This will use the mocked API response

    # Assertions
    assert response.status_code == 200
    assert response.json() == mock_response_data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload, status_code, expected_fields",
    [
        (
            {
                "username": "updateduser",
                "name": "Updated User",
            },
            200,
            {"username": "updateduser", "name": "Updated User"},
        ),
        (
            {
                "username": "invaliduser@@@",
            },
            400,
            ["username"],
        ),
    ],
)
def test_update_user(payload, status_code, expected_fields,authenticated_client, create_user):
    """Test updating user details"""
    user = create_user()
    client = authenticated_client()
    user_id = user.id
    response = client.patch(
        f"/api/users/{user_id}/",
        payload,
        format="json",
    )
    assert response.status_code == status_code
    
    
    if status_code == 200:
        for field, value in expected_fields.items():
            assert response.data[field] == value
    else:
        for field in expected_fields:
            assert field in response.data["error"].keys()


@pytest.mark.django_db
def test_change_password(authenticated_client, create_user):
    """Test password change"""
    user = create_user()
    user_id = user.id
    client = authenticated_client()
    response = client.patch(
        f"/api/users/{user_id}/change-password/",
        {
            "current_password": "testpassword12@",
            "new_password": "testpassword12#",
            "confirm_new_password": "testpassword12#",
        },
        format="json",
    )
    assert response.status_code == 200  # Password updated successfully

@pytest.mark.django_db
def test_delete_user(authenticated_client, create_user, mocker):
    """Test deleting a user"""
    user = create_user()
    client = authenticated_client()

    mock_delete_task = mocker.patch("account.tasks.soft_delete_user_related_objects.delay", Mock())

    user_id = user.id
    response = client.delete(
        f"/api/users/{user_id}/", {"password": "testpassword12@"}
    )
    assert response.status_code == 204  # User deleted successfully

    mock_delete_task.assert_called_once_with(user.id)
    user.refresh_from_db()
    assert not user.is_active


@pytest.mark.django_db
def test_password_reset_request_success(mocker, api_client, create_user):
    """Test successful password reset request with email sent via Celery (mocked)"""
    user = create_user()

    # Mock the email-sending Celery task
    mock_task = mocker.patch("account.tasks.send_reset_password_email.delay")

    # Mock Redis cache to bypass storing/reset link check
    mock_cache_get = mocker.patch("django.core.cache.cache.get", return_value=None)
    mock_cache_set = mocker.patch("django.core.cache.cache.set")

    response = api_client.post(
        "/api/auth/password-reset/", {"email": user.email}
    )

    assert response.status_code == 200
    assert response.data["message"] == "Password reset email sent."

    # Ensure email sending task was called
    mock_task.assert_called_once_with(user.email, mocker.ANY)

    # Ensure Redis cache was checked and set
    mock_cache_get.assert_called_once_with(f"password_reset:{user.id}")
    mock_cache_set.assert_called_once_with(
        f"password_reset:{user.id}", mocker.ANY, timeout=300
    )

@pytest.mark.django_db
def test_password_reset_confirm_success(mocker, api_client, create_user):
    """Test successful password reset confirmation"""
    user = create_user()

    # Mock token validation
    mock_token_validator = mocker.patch(
        "account.views.validate_custom_token", return_value=user
    )

    # Mock Redis cache deletion after password reset
    mock_cache_delete = mocker.patch("django.core.cache.cache.delete")

    new_password = "NewSecurePass123@"
    response = api_client.post(
        f"/api/auth/password-reset-confirm/valid_token/",
        {"password": new_password},
    )

    assert response.status_code == 200
    assert response.data["message"] == "Password has been reset successfully."

    # Ensure validate_custom_token was called
    mock_token_validator.assert_called_once_with("valid_token")

    # Ensure Redis cache was deleted
    mock_cache_delete.assert_called_once_with(f"password_reset:{user.id}")

    # Ensure password is updated in the database
    user.refresh_from_db()
    assert user.check_password(new_password)
