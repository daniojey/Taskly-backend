import traceback

from django.conf import settings
from django.test.testcases import BaseDatabaseWrapper
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from api.tests.factories.group_factory import GroupFactory
from api.tests.factories.user_factory import (
    UserFactory,
)

@pytest.fixture(autouse=True)
def trace_db_close(monkeypatch):
    original = BaseDatabaseWrapper.close

    def close(self):
        print("\n=== DB connection close() called from: ===")
        traceback.print_stack()
        return original(self)

    monkeypatch.setattr(BaseDatabaseWrapper, "close", close)

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def custom_user():
    return UserFactory

@pytest.fixture
def users():
    return UserFactory


@pytest.fixture
def user_password():
    return "testpass123"


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def auth_client_for(api_client):
    def _make(user):
        refresh = RefreshToken.for_user(user)
        api_client.cookies.load({
            "refresh": str(refresh)
        })
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return api_client
    return _make

@pytest.fixture
def auth_api_client(api_client, user):

    refresh = RefreshToken.for_user(user)
    api_client.cookies.load({
        "refresh": str(refresh)
    })
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def user_with_groups():
    u = UserFactory()
    g1, g2, g3 = GroupFactory.create_batch(
        3, 
        group="user", 
        members=[user],
        owner=u
    )

    return u

@pytest.fixture
def group(user):
    return GroupFactory.create(owner=user)

@pytest.fixture
def groups():
    return GroupFactory


