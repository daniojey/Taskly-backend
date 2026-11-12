from django.conf import settings
import pytest
from django.urls import reverse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from main.utils.custom_api_errors import NotFoundRefreshToken
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
        pytest.param("", 404),
        pytest.param("4456456456456456", 401),
        pytest.param("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30", 401)
    ])
    def test_verify_invalid_token(self, client, status, token, user):
        response = client.post(self.verify_url, {"token": token})

        assert response.status_code == status

    @pytest.mark.parametrize("method,", [
        pytest.param("get"),
        pytest.param("put"),
        pytest.param("patch"),
        pytest.param("delete")
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
    samesite = settings.CSRF_COOKIE_SAMESITE
    secure = settings.CSRF_COOKIE_SECURE

    @pytest.mark.parametrize("secure",[
        pytest.param(False),
        pytest.param(True)
    ])
    def test_token_pair(
        self, 
        api_client, 
        user, 
        user_password, 
        secure,
        settings):
        settings.CSRF_COOKIE_SECURE = secure

        test_data = {
            "username": user.username,
            "password": user_password
        }

        response = api_client.post(self.pair_url, test_data)

        assert response.status_code == 200, response
        assert response.cookies['refresh'], response.cookies

        refresh_data = response.cookies['refresh']

        assert int(refresh_data['max-age']) == self.max_age[0]
        assert refresh_data['httponly'] == True, refresh_data['httponly']
        assert refresh_data['samesite'] == self.samesite, refresh_data

        if secure == True:
            assert refresh_data['secure'] == True, refresh_data

        data = response.data

        assert data['access']
        assert data['user']['username'] == user.username
        assert int(data['user']['id']) == user.id

    @pytest.mark.parametrize("has_username, password, status_code, error", [
        pytest.param(True, "uncorrect", 401, None),
        pytest.param(False, "uncorrect", 401, TypeError),
        pytest.param(True, None, 400, TypeError),
        pytest.param(False, None, 400, TypeError)
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

    @pytest.mark.parametrize("method", ['get', 'put', 'patch', 'delete'])
    def test_not_allowed_methods(self, method, api_client):
        response = getattr(api_client, method)(self.pair_url)

        assert response.status_code == 405


@pytest.mark.django_db
class TestCustomTokenRefresh:
    pair_url = reverse("api:token_obtain_pair", kwargs={"version": "v1"})
    refresh_url = reverse("api:token_refresh", kwargs={'version': 'v1'})

    def test_refresh_token_url(self, api_client, user, user_password):
        pair_data = {
            'username': user.username,
            'password': user_password
        }

        # We`re going to simulate get real token and refresh it `
        r = api_client.post(self.pair_url, pair_data)
        assert r.status_code == 200, r

        old_token = r.cookies['refresh'].value

        assert old_token

        response = api_client.post(self.refresh_url)

        assert response.status_code == 200

        new_token = response.cookies['refresh'].value

        with pytest.raises(TokenError):
            RefreshToken(old_token)

        RefreshToken(new_token)

        assert old_token != new_token

    @pytest.mark.parametrize('token, status', [
        pytest.param('', 404),
        pytest.param(None, 401),
        pytest.param("gdfgfdgdfg", 401),
    ])
    def test_hearing_of_exceptions(
        self, 
        api_client,
        user,
        user_password,
        token,
        status,
        ):
        user_data = {
            'username': user.username,
            'password': user_password
        }

        # First step take valid refresh token
        r = api_client.post(self.pair_url, user_data)

        assert r.status_code == 200

        r.cookies['refresh'] = token

        # with pytest.raises(error):
        response = api_client.post(self.refresh_url)

        assert response.status_code == status


    @pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
    def test_not_allowed_methods(self, api_client, method):
        response = getattr(api_client, method)(self.refresh_url)

        assert response.status_code == 405