import pytest
from rest_framework.test import APIClient
from account.models import User,ActiveAccessToken
from rest_framework_simplejwt.tokens import AccessToken
from categories.models import Category
from django.utils.text import slugify

@pytest.fixture
def api_client():
    """Returns a Django API test client"""
    return APIClient()

@pytest.fixture
def create_user(db):
    """Fixture to create a dynamic test user."""
    def _create_user(username="testuser", password="testpassword12@",  email="testuser@example.com", name="Test user"):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            name=name
        )
        return user
    return _create_user

@pytest.fixture
def generate_token():
    def _generate_token(username = "testuser", password = "testpassword12@"):
        user = User.objects.get(username=username)
        access_token = str(AccessToken.for_user(user))

        # Store the active access token in the database
        ActiveAccessToken.objects.create(user=user, access_token=access_token)
        return access_token
    
    return _generate_token


@pytest.fixture
def authenticated_client(api_client, generate_token):
    """Fixture to return an authenticated client using the login_user fixture"""
    
    def _authenticated_client(username="testuser", password="testpassword12@"):
        """Authenticates a user and returns the authenticated API client"""
        access_token = generate_token(username, password)
        
        assert access_token  # Ensure the token exists
        # Set authorization header for the client
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        return api_client

    return _authenticated_client


# @pytest.fixture
# def authenticated_client(api_client):
#     """Fixture to return an authenticated client with a valid access token"""
#     print("running authenticated_client")
#     login_response = api_client.post(
#         "/api/auth/login/",
#         {"username": "testuser", "password": "testpassword12@"},
#         format="json",
#     )
#     assert login_response.status_code == 200  # Ensure login was successful

#     access_token = login_response.data["access_token"]
#     api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")  # Set auth header
#     return api_client
     
#category fixtures 

@pytest.fixture
def create_category(db, create_user):
    """Fixture to create a category for a user"""
    def _create_category(name="Test Category", user=None, type="debit"):
        user = user or create_user()
        category = Category.objects.create(
            name=name,
            slug=slugify(name),
            user=user,
            type=type,
        )
        return category
    return _create_category

#wallet fixtures
from wallets.models import Wallet

@pytest.fixture
def create_wallet(db, create_user):
    """Fixture to create a wallet for a user"""
    def _create_wallet(name="Test Wallet", user=None):
        user = user or create_user()
        wallet = Wallet.objects.create(
            name=slugify(name),
            user=user,
        )
        return wallet
    return _create_wallet