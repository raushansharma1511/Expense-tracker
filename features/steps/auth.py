from behave import given, when, then
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@given('a user is registered with username "{username}" and password "testpassword12@"')
def step_given_user_registered(context, username):
    User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpassword12@",
        name="Test User",
    )
    context.client = APIClient()


@when('a user registers with the username "{username}", email "{email}", password "{password}", and name "{name}"')
def step_register_user_with_params(context, username, email, password, name):
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "name": name
    }
    print("Payload is:", payload)
    context.response = context.client.post("/api/auth/register/", payload, format="json")
    print("Register Response:", context.response.status_code, context.response.data)



@when(
    'the user logs in with username "{login_username}" and password "{login_password}"'
)
def step_user_login(context, login_username, login_password):
    payload = {"username": login_username, "password": login_password}
    context.client = APIClient()
    context.response = context.client.post("/api/auth/login/", payload, format="json")
    print("Login Response:", context.response.status_code, context.response.data)

    # Store auth header if successful
    if context.response.status_code == 200 and "access_token" in context.response.data:
        token = context.response.data["access_token"]
        context.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


@then("the response status code should be {status_code:d}")
def step_status_code_check(context, status_code):
    assert (
        context.response.status_code == status_code
    ), f"Expected status {status_code}, got {context.response.status_code}"


@then("the response should contain fields: {fields}")
def step_check_fields(context, fields):
    if not fields.strip():
        return  # Skip empty check

    expected_fields = [f.strip() for f in fields.split(",")]
    for field in expected_fields:
        assert (
            field in context.response.data
        ), f"Expected field '{field}' not in response"



@when('the user sends a POST request to "/api/auth/logout/"')
def step_logout(context):
    context.response = context.client.post("/api/auth/logout/")
    print("Logout Response:", context.response.status_code, context.response.data)
