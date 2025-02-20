import pytest
from django.urls import reverse
from unittest.mock import patch
from unittest.mock import Mock
from uuid import UUID

@pytest.mark.django_db
def test_create_transaction(
    create_user, create_category, create_wallet, authenticated_client, mocker
):
    """Test creating a transaction while mocking the Celery task"""

    user = create_user()
    category = create_category(user=user)
    wallet = create_wallet(user=user)
    client = authenticated_client()

    url = reverse("transaction-list-create")
    payload = {
        "user": user.id,
        "category": category.id,
        "wallet": wallet.id,
        "amount": 100,
        "description": "test transaction",
    }

    # Mock Celery Task
    mock_task = mocker.patch("transactions.tasks.handle_transaction.delay")

    response = client.post(url, payload)

    assert response.status_code == 201
    assert response.data["amount"] == "100.00"
    assert response.data["user"] == user.id
    assert response.data["category"] == category.id
    assert response.data["wallet"] == wallet.id
    initial_balance = wallet.balance
    wallet.refresh_from_db()
    current_balance = wallet.balance
    assert current_balance == initial_balance - float(response.data["amount"])
    
    mock_task.assert_called_once_with(UUID(response.data["id"]))
    
@pytest.mark.django_db
def test_create_transaction_fail(
    create_user, create_category, create_wallet, authenticated_client, mocker
):
    """Test creating a transaction while mocking the Celery task"""

    user1 = create_user()
    user2= create_user(username="testuser2", password="testpassword2@", email="testuser2@gmail.com")
    category = create_category(user=user1)
    wallet = create_wallet(user=user2)
    client = authenticated_client()

    url = reverse("transaction-list-create")
    payload = {
        "user": user1.id,
        "category": category.id,
        "wallet": wallet.id,
        "amount": 100,
        "description": "test transaction",
    }

    # Mock Celery Task
    mock_task = mocker.patch("transactions.tasks.handle_transaction.delay")

    response = client.post(url, payload)

    assert response.status_code == 400
    assert "error" in response.data
    assert "wallet" in response.data["error"].keys()

    
    mock_task.assert_not_called()