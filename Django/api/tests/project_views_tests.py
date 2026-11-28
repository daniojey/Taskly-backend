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


@pytest.mark.django_db
class TestGetProjects:
    list_url = get_url('api:groups-projects-list')

    @pytest.mark.parametrize('projects_count,', [0, 3, 5, 10])
    def test_get_projects(
            self, 
            auth_api_client,
            user,
            group,
            projects,
            projects_count
    ):
        projects.create_batch(projects_count, owner=user, group=group)

        response = auth_api_client.get(self.list_url)

        assert response.status_code == 200, response.data
        data = response.data['results'][0]['projects']

        assert len(data) == projects_count, data


    @pytest.mark.parametrize('user_type, projects_count, status, expected_count', [
        ('owner', 2, 200, 2),
        ('owner', 0, 200, 0),
        ('ungroup_user', 2, 200, 0),
        ('ungroup_user', 0, 200, 0)
    ])
    def test_get_projects(
        self,
        projects,
        auth_client_for,
        users,
        user_type, projects_count, status, expected_count
    ):
        new_user = users.create()
        is_owner = True if user_type == 'owner' else False

        projects(projects_count, new_user, is_owner)

        new_client = auth_client_for(new_user)

        response = new_client.get(self.list_url)

        assert response.status_code == status

        if user_type == 'owner':
            data = response.data['results'][0]['projects']

            assert len(data) == expected_count
        else:
            data = response.data['results']

            assert len(data) == expected_count


    def test_anon_user(
            self,
            api_client
    ):
        response = api_client.get(self.list_url)

        assert response.status_code == 401