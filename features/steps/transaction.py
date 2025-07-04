from behave import given, when, then
from django.urls import reverse
from decimal import Decimal
from transactions.models import Transaction
from uuid import UUID
from unittest.mock import patch
import transactions.tasks

@given("a user with a wallet and categories")
def step_user_wallet_category(context):
    print("current user and client is", context.user, context.client)
    context.wallet.refresh_from_db()
    context.current_balance = context.wallet.balance


@when('the user performs a "{type}" transaction of "{amount}" with description "{description}"')
def step_perform_transaction(context, type, amount, description):
    category = context.credit_category if type == "credit" else context.debit_category

    payload = {
        "user": str(context.user.id),
        "wallet": str(context.wallet.id),
        "category": str(category.id),
        "type": type,
        "amount": amount,
        "description": description,
    }

    url = reverse("transaction-list-create")
    with patch("transactions.tasks.handle_transaction.delay") as mock_celery:
        context.response = context.client.post(url, payload)

        assert context.response is not None, "No response received"
        context.response_data = context.response.data

        # Update wallet object after transaction
        context.wallet.refresh_from_db()


@then("the transaction response status code should be 201")
def step_assert_status(context):
    assert context.response.status_code == 201, f"Expected 201, got {context.response.status_code}"


@then("the transaction response should contain fields: {fields}")
def step_assert_response_fields(context, fields):
    expected_fields = [field.strip() for field in fields.split(",")]
    for field in expected_fields:
        assert field in context.response_data, f"Missing field '{field}' in response"


@then("the wallet balance should be \"{expected_balance}\"")
def step_assert_wallet_balance(context, expected_balance):
    actual_balance = context.wallet.balance
    assert actual_balance == Decimal(expected_balance), (
        f"Expected balance {expected_balance}, got {actual_balance}"
    )
