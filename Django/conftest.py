import traceback

from django.test.testcases import BaseDatabaseWrapper
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from api.tests.factories.project_factory import ProjectFactory
from users.models import Notification, User
from api.tests.factories.notification_factory import NotificationFactory
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

@pytest.fixture
def group_with_member(user):

    def _make(members = tuple()):
        return GroupFactory(owner=user, members=members)

    return _make


@pytest.fixture
def notification():

    def _make(user, select_type=Notification.INVITE_MESSAGE, group_id=None):
        return NotificationFactory(
            notify_type=select_type,
            user=user,
            data={'group_id': group_id} if group_id else {},
            is_read=False
        )

    return _make


@pytest.fixture
def notify_invalid_data():
    def _make(new_user, notify, expected_exclude = ''):
        """
        example_format = {
            'type': 'accept',
            'notify': {
                'id': notify.id,
                'user': {
                    'id':user.id,
                    'username': user.username
                }
            }
        }
        """

        exclude = expected_exclude.split(',')

        new_data = {
            'type': 'accept',
            'notify': {
                'id': notify.id,
                'user': {
                    'id':new_user.id,
                    'username': new_user.username
                }
            }
        }

        if 'type' in exclude:
            del new_data['type']

        if 'notify_id' in exclude:
            del new_data['notify']['id']

        if 'user' in exclude:
            del new_data['notify']['user']

        if 'notify' in exclude:
            del new_data['notify']

        return new_data

    return _make


@pytest.fixture
def project_data(group):
    def _make(exclude, custom_user=None, custom_group=None):
        """
        example correct config
        """
        test_data = {
            'group': custom_group.id if custom_group else group.id,
            'title': f'Test title {group.id}',
            'description': 'Test description'
        }

        if exclude == 'group':
            del test_data['group']

        if exclude == 'title':
            del test_data['title']

        if exclude == 'description':
            del test_data['description']

        return test_data

    return _make


@pytest.fixture
def project(user, group):
    return ProjectFactory(owner=user, group=group)


@pytest.fixture
def projects(user, groups):

    def _make(count, new_user=None, owner=False):

        if new_user and owner:
            group = groups.create(owner=new_user)
        else:
            group = groups.create(owner=user)
        
        if new_user:
            if owner:
                res = ProjectFactory.create_batch(count, owner=new_user, group=group)
            else:
                res = ProjectFactory.create_batch(count, group=group)
        else:
            res = ProjectFactory.create_batch(count, owner=user, group=group)

        return res

    return _make
