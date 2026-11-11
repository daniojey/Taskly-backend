from django.conf import settings
import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from api.serializers.user_serializers import UserSerializer

@pytest.mark.django_db
class TestCustomTokenVerify:
    verify_url = reverse("api:token_verify", kwargs={"version": "v1"})

    def test_verify_valid_token(self, api_client, user):
        refresh = RefreshToken.for_user(user)

        response = api_client.post(self.verify_url, {'token': refresh.access_token})

        assert response.status_code == 200
        assert response.data['user']
        assert response.data['user'] == UserSerializer(user).data
        assert response.data['message'] == "Token is valid"

    @pytest.mark.parametrize("token, status", [
        ("", 404),
        ("4456456456456456", 401),
        ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30", 401)
    ])
    def test_verify_invalid_token(self, client, status, token, user):
        response = client.post(self.verify_url, {"token": token})

        assert response.status_code == status

    @pytest.mark.parametrize("method,", [
        ("get"),
        ("put"),
        ("patch"),
        ("delete")
    ])
    def test_another_methods(self, api_client, method):
        match (method):
            case "get":
                res = api_client.get(self.verify_url)
            case "put":
                res = api_client.put(self.verify_url, {"token": "1234"})
            case "patch":
                res = api_client.patch(self.verify_url, {"token": "1234"})
            case "delete":
                res = api_client.delete(self.verify_url)

        # Expected not allowed
        assert res.status_code == 405


@pytest.mark.django_db
class TestCustomTokenPair:
    pair_url = reverse("api:token_obtain_pair", kwargs={"version": "v1"})
    max_age = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),

    def test_token_pair(self, api_client, user, user_password):
        test_data = {
            "username": user.username,
            "password": user_password
        }

        response = api_client.post(self.pair_url, test_data)

        assert response.status_code == 200
        assert response.cookies['refresh']
        assert int(response.cookies['refresh']['max-age']) == self.max_age[0]
        assert response.cookies['refresh']['httponly'] == True

        data = response.data

        assert data['access']
        assert data['user']['username'] == user.username
        assert int(data['user']['id']) == user.id

    @pytest.mark.parametrize("has_username, password, status_code, error", [
        (True, "uncorrect", 401, None),
        (False, "uncorrect", 401, TypeError),
        (True, None, 400, TypeError),
        (False, None, 400, TypeError)
    ])
    def test_not_valid_data(
        self, 
        has_username,
        user,
        api_client, 
        password, 
        status_code,
        error
        ):

        test_data = {
            'username': user.username if has_username else None,
            'password': password
        }

        if error:
            with pytest.raises(error):
                response = api_client.post(self.pair_url, test_data)
        else:
            response = api_client.post(self.pair_url, test_data)
        
            assert response.status_code == status_code