import pytest
from account.serializers import UserSerializer


@pytest.mark.django_db
def test_user_serializer_valid(create_user):
    """Test user serializer with valid data"""
    user = create_user(username="serializeruser", password="serializerpass1@", email="serializeruser@gmail.com",name = "Serializer User")
    serializer = UserSerializer(user)
    data = serializer.data

    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["name"] == user.name

@pytest.mark.django_db
def test_user_serializer_invalid():
    """Test user serializer with invalid data"""
    payload = {"username": "serializeruser", "email": "invalid_email", "password": "short"}
    serializer = UserSerializer(data = payload)
    
    assert not serializer.is_valid()
    
    assert "email" in serializer.errors
    assert "password" in serializer.errors
    assert "name" in serializer.errors
    