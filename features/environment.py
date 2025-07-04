from behave import fixture, use_fixture
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from account.models import User, ActiveAccessToken
from wallets.models import Wallet
from categories.models import Category
from django.utils.text import slugify

User = get_user_model()


@fixture
def api_client(context):
    print("initailizing the client")
    context.client = APIClient()


def before_all(context):
    use_fixture(api_client, context)


@fixture
def create_authenticated_client(context):
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword12@",
        "name": "Test User",
    }

    # Register
    response = context.client.post("/api/auth/register/", user_data)
    if response.status_code != 201:
        print("Registration failed", response.json())
        assert False

    # Login
    response = context.client.post(
        "/api/auth/login/",
        {
            "username": user_data["username"],
            "password": user_data["password"],
        },
    )
    token = response.json()["access_token"]
    context.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    context.auth_headers = {"Authorization": f"Bearer {token}"}
    context.user = User.objects.get(username=user_data["username"])


@fixture
def authenticated_client_with_categories_and_wallet(context):
    user = User.objects.create_user(
        username="featureuser",
        email="feature@example.com",
        password="Password123!",
        name="Feature User",
    )
    context.user = user

    # Auth
    token = str(AccessToken.for_user(user))
    ActiveAccessToken.objects.create(user=user, access_token=token)
    
    context.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # Wallet
    wallet = Wallet.objects.create(name="feature-wallet", user=user)
    context.wallet = wallet

    # Categories
    context.debit_category = Category.objects.create(
        name="Food", slug=slugify("Food"), user=user, type="debit"
    )
    context.credit_category = Category.objects.create(
        name="Salary", slug=slugify("Salary"), user=user, type="credit"
    )


def before_scenario(context, scenario):
    if "authenticated" in scenario.tags:
        use_fixture(create_authenticated_client, context)
    
    if 'authenticated_client_with_categories_and_wallet' in scenario.tags:
        use_fixture(authenticated_client_with_categories_and_wallet, context)


# def before_feature(context, feature):
#     if 'authenticated_client_with_categories_and_wallet' in feature.tags:
#         use_fixture(authenticated_client_with_categories_and_wallet, context)
