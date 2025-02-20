import pytest
from categories.models import Category

@pytest.mark.django_db
def test_category_creation(create_category):
    """Test if a category is created successfully"""
    category = create_category()
    assert Category.objects.count() == 1
    assert category.name == "Test Category"

@pytest.mark.django_db
def test_category_soft_delete(create_category):
    """Test soft deletion of a category"""
    category = create_category()
    category.is_deleted = True
    category.save()
    
    assert category.is_deleted is True

@pytest.mark.django_db
def test_category_str_representation(create_category):
    """Test category string representation"""
    category = create_category(name="Food")
    assert str(category) == "Food"
