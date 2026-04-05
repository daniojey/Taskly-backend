

from pytest import fixture
import pytest
from pytest_config import api_url

from users.models import User


def groups_count(parser):
    parser.addoption(
        "--groups-count",
        action='store',
        default=5,
        type=int,
        help="The number of groups that will be created"
    )

@fixture(scope="function")
def auth_data(request , django_db_setup, django_db_blocker):
    username = request.param

    with django_db_blocker.unblock():
        user = User.objects.get(username=username)

    from rest_framework_simplejwt.tokens import RefreshToken
    token = RefreshToken.for_user(user)

    return {
        'token': str(token.access_token),
        'user': user,
        'username': user.username
    }


@pytest.fixture(autouse=True, scope="session")
def create_users(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        User.objects.create_user(username="base_user",  password="base_user123")
        User.objects.create_user(username="owner_user", password="owner_user123", is_staff=True)
        User.objects.create_user(username="admin_user", password="admin_user",    is_superuser=True)
    
    yield
    
    with django_db_blocker.unblock():
        User.objects.all().delete()