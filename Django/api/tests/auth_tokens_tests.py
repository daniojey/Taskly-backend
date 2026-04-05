import pytest
from pytest_config import api_url


@pytest.mark.django_db
@pytest.mark.parametrize("username, password",[
    ('base_user', 'base_user123'),
    ('admin_user', 'admin_user'),
])
class TestTokens:
    def test_get_access_token(self, client, username, password):
        response = client.post(api_url + 'token/', {'username': username, 'password': password})
        assert response.status_code == 200


    def test_availabily_refresh_token(self, client, username, password):
        response = client.post(api_url + 'token/', {'username': username, 'password': password})

        assert response.status_code == 200
        assert response.cookies.get('refresh')


    def test_verify_token(self, client, username, password):
        response = client.post(api_url + 'token/', {'username': username, 'password': password})
        access_token = response.data['access']
        response = client.post(api_url + 'token/verify/',
                               {'token': access_token},
        )

        assert response.status_code == 200
        user = response.data['user']

        assert user['id']
        assert user['username']


    def test_refresh_access_token(self, client, username, password):
        response = client.post(api_url + 'token/', {'username': username, 'password': password})
        refresh_token = response.cookies.get('refresh').value
        data = response.data

        assert response.status_code == 200
        assert data['access']
        assert refresh_token

        client.cookies['refresh'] = refresh_token
        response = client.post(api_url + 'token/refresh/')
        new_refresh_token = response.cookies.get('refresh')

        assert response.status_code == 200
        assert response.data['access']
        assert new_refresh_token
        assert refresh_token != new_refresh_token
        


    def test_logout_token(self, client, username, password):
        response = client.post(api_url + 'token/', {'username': username, 'password': password})

        assert response.status_code == 200
        assert response.cookies.get('refresh')

        response = client.post(api_url + 'token/logout/')

        refresh = response.cookies.get('refresh').value

        assert not refresh


@pytest.mark.django_db
class TestTokenWithoutData:
    def test_get_token_failure_data(self, client):
        request = client.post(api_url + 'token/', {'username': 'user', 'password': 'user123'})

        assert request.status_code == 401

    def test_get_access_token_without_refresh(self, client):
        response = client.post(api_url + 'token/refresh/')

        assert response.status_code == 404
        assert response.data['message'] == 'Token not found'


    @pytest.mark.parametrize('token, status', [
        ("", 404),
        ("token123", 401),
    ])
    def test_verify_token_failed_data(self, client, token, status):
        response = client.post(api_url + 'token/verify/', {'token': token})

        assert response.status_code == status

