import pytest
from rest_framework.test import APIClient
from django.urls import reverse


@pytest.mark.django_db
def test_create_category(create_user, authenticated_client):
    """Test category creation via API"""
    user = create_user()
    client = authenticated_client()
    
    url = reverse("category-list-create-view")
    data = {"name": "Bills", "user": str(user.id), "type": "debit"}
    response = client.post(url, data)

    assert response.status_code == 201
    assert response.data["name"] == "Bills"
    
@pytest.mark.django_db
def test_get_categories(create_category, create_user, authenticated_client):
    """Test retrieving categories"""
    user = create_user()
    client = authenticated_client()

    create_category(name="Rent", user=user)
    
    url = reverse("category-list-create-view")
    response = client.get(url)
    
    assert response.status_code == 200
    assert response.data["items"][0]["name"] == "Rent"
    

@pytest.mark.django_db
def test_update_category(create_category, create_user, authenticated_client):
    """Test category update via API"""
    user = create_user()
    client = authenticated_client()

    category = create_category(name="Shopping", user=user)
    url = reverse("category-detail-view", kwargs={"pk": category.id})
    data = {"name": "Groceries"}

    response = client.patch(url, data)
    
    assert response.status_code == 200
    assert response.data["name"] == "Groceries"
    
@pytest.mark.django_db
def test_delete_category(create_category, create_user, authenticated_client):
    """Test soft deletion of a category via API"""
    user = create_user()
    client = authenticated_client()

    category = create_category(name="Travel", user=user)
    url = reverse("category-detail-view", kwargs={"pk": category.id})

    response = client.delete(url)
    
    assert response.status_code == 204
    category.refresh_from_db()
    assert category.is_deleted is True