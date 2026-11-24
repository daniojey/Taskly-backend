
import pytest

from main.utils.custom_api_errors import ForbiddenProject
from task.models import Project
from api.tests.utils.common import get_url

@pytest.mark.django_db
class TestProjectCreate:

    create_url = get_url('api:groups-projects-list')

    def test_create_project(
            self,
            user,
            group,
            auth_api_client
    ):
        assert not Project.objects.filter(
            owner=user, 
            group=group, 
            title='Test Title', 
            description='Test description'
        ).exists()
        
        test_data = {
            'group': group.id,
            'title': 'Test Title',
            'description': 'Test description'
        }

        response = auth_api_client.post(self.create_url, data=test_data, format='json')

        assert response.status_code == 201, response.data
        assert Project.objects.filter(
            group=group, 
            title='Test Title', 
            description='Test description'
        ).exists()


    def test_no_owner(
            self,
            users,
            auth_client_for,
            group,
    ):
        user = users.create()

        assert group.owner_id != user.id
        test_data = {
            'group': group.id,
            'title': 'Test title',
            'description': 'Description'
        }

        api_client = auth_client_for(user)
        response = api_client.post(self.create_url, data=test_data, format='json')

        assert response.status_code == 403, response.data

    @pytest.mark.parametrize('exclude_field, status', [
        pytest.param('group', 404), 
        pytest.param('title', 400), 
    ])
    def test_not_valid_data(
            self, 
            user,
            group,
            auth_api_client,
            project_data,
            exclude_field,
            status
    ):
        test_data = project_data(exclude_field)
        response = auth_api_client.post(self.create_url, data=test_data, format='json')

        assert response.status_code == status


    def test_not_authenticate(
            self,
            api_client,
            project_data
    ):
        test_data = project_data(None)
        response = api_client.post(self.create_url, data=test_data, format='json')

        assert response.status_code == 401