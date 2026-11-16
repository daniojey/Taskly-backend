import pytest

from api.tests.utils.common import get_url


@pytest.mark.django_db
class TestGroupCreate:
    create_url = get_url("api:groups-list")
    valid_group_data = {
        
    }

    @pytest.mark.parametrize("members_count", [0, 5, 10, 15])
    def test_created_group(self, auth_api_client, user, users, members_count):
        users = users.create_batch(members_count)
        users_ids = [int(u.id) for u in users]
        print(users_ids)

        group_data = {
            'name': 'TestGroupName',
            'members': [*users_ids] if users_ids else []
        }

        response = auth_api_client.post(self.create_url, group_data, format='json')

        assert response.status_code == 201, response.data['members']
        data = response.data['results']

        assert 'id' in data
        assert 'name' in data
        assert data['name'] == group_data['name']
        assert data['owner'] == user.id
        assert 'created_at' in data
        assert 'updated_at' in data
        assert user.id in data['members']

        if members_count > 0:
            assert {*users_ids, user.id} == set(data['members'])


    @pytest.mark.parametrize("name, members, status,",[
        pytest.param('TestGroup', 'lol it`s not valid', 400, id="Members[] but get string"),
        pytest.param('', [], 400, id="Not valid name for group"),
        pytest.param(None, ['gdg', 'gsdg', 'gsdg'], 400, id="Not valid name None and membrs ['gdg', 'gsdg', 'gsdg'] fields"),
        pytest.param({}, '', 400, id="Not valid name {} and members '' fiedls "),
        pytest.param('TestGroup', [99999999, 10000900], 400, id="Expected these users is not exist")
    ] )
    def test_not_valid_data(self, auth_api_client, name, members, status):
        group_data = {
            'name': name,
            'members': members
        }

        response = auth_api_client.post(self.create_url, group_data, format='json')

        assert response.status_code == status, response.data


    def test_not_authenticate_user(self, api_client):
        group_data = {
            'name': "TestGroup",
            'members': []
        }

        response = api_client.post(self.create_url, group_data, format='json')

        assert response.status_code == 401