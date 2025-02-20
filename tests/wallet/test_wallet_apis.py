import pytest
from rest_framework import status
from django.urls import reverse


@pytest.mark.django_db
def test_create_wallet(create_user, authenticated_client):
    user = create_user()
    client = authenticated_client()

    url = reverse("wallet-list-create-view")
    data = {"name": "My Wallet", "user": user.id}
    response = client.post(url, data)

    assert response.status_code == 201
    assert response.data["name"] == "My Wallet"
    assert response.data["user"] == user.id


# def test_update_wallet_normal_user(self, authenticated_client, normal_user, wallet):
#     url = reverse('wallet-detail', args=[wallet.id])
#     data = {'name': 'Updated Wallet Name'}
#     authenticated_client.force_authenticate(user=normal_user)
#     response = authenticated_client.patch(url, data, format='json')
#     assert response.status_code == status.HTTP_200_OK
#     assert response.data['name'] == 'Updated Wallet Name'

# def test_update_wallet_staff_user(self, authenticated_client, staff_user, wallet):
#     url = reverse('wallet-detail', args=[wallet.id])
#     data = {'name': 'Updated by Staff'}
#     authenticated_client.force_authenticate(user=staff_user)
#     response = authenticated_client.patch(url, data, format='json')
#     assert response.status_code == status.HTTP_200_OK
#     assert response.data['name'] == 'Updated by Staff'

# def test_delete_wallet_normal_user(self, authenticated_client, normal_user, wallet):
#     url = reverse('wallet-detail', args=[wallet.id])
#     authenticated_client.force_authenticate(user=normal_user)
#     response = authenticated_client.delete(url)
#     assert response.status_code == status.HTTP_204_NO_CONTENT

# def test_delete_wallet_staff_user(self, authenticated_client, staff_user, wallet):
#     url = reverse('wallet-detail', args=[wallet.id])
#     authenticated_client.force_authenticate(user=staff_user)
#     response = authenticated_client.delete(url)
#     assert response.status_code == status.HTTP_204_NO_CONTENT
