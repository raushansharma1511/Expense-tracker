import pytest
from categories.serializers import CategorySerializer

@pytest.mark.django_db
def test_category_serializer_valid(create_category, create_user):
    """Test category serializer with valid data"""
    category = create_category(user=create_user())
    data = CategorySerializer(category).data

    assert data["name"] == category.name
    assert str(data["user"]) == str(category.user.id)
    assert data["type"] == category.type

@pytest.mark.django_db
def test_category_serializer_invalid_user():
    """Test category serializer with an invalid user"""
    invalid_data = {"name": "Test", "user": None, "type": "debit"}

    serializer = CategorySerializer(data=invalid_data)
    assert not serializer.is_valid()
    assert "user" in serializer.errors
