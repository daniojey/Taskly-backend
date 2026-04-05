from users.models import Group, User
from pytest_config import api_url, create_groups_count
import pytest


@pytest.fixture(scope='class')
def create_groups(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        owner_user = User.objects.get(username='owner_user')
        all_users_ids = User.objects.all().values_list('id', flat=True)

        groups = []
        for i in range(create_groups_count):
            group = Group(
                name=f"Group name {i}",
                owner=owner_user,
            )
            groups.append(group)

        created = Group.objects.bulk_create(groups)

        for group in created:
            group.members.set(all_users_ids)

    yield

    with django_db_blocker.unblock():
        Group.objects.all().delete()


@pytest.mark.django_db
@pytest.mark.usefixtures('create_groups')
@pytest.mark.parametrize('auth_data, username', [
    ('base_user', 'base_user'), 
    ('owner_user', 'owner_user'), 
    ('admin_user', 'admin_user')
], indirect=['auth_data'])
class TestGroups:
    def test_get_group_list(self, client, auth_data, username):
        response = client.get(api_url + 'groups/', headers={
            "AUTHORIZATION": f"Bearer {auth_data['token']}"
        })

        assert response.status_code == 200
        data = response.data

        assert data['results']
        assert len(data['results']) == create_groups_count

        groups_ids = Group.objects.all().values_list('id', flat=True)
        groups = data['results']

        for group in groups:
            assert group['id'] in groups_ids

    
    @pytest.mark.parametrize('group_id, status', [
        (1, 200),
        (9999999999, 404),
    ])
    def test_get_retrieve_group(
        self, 
        client, 
        auth_data, 
        username,
        group_id,
        status,
        ):

        response = client.get(api_url + f"groups/{group_id}/", headers={
            'AUTHORIZATION': f"Bearer {auth_data['token']}"
        })

        assert response.status_code == status

        if status == 200:
            data = response.data

            assert data['results']

            group = data['results']

            assert group['members']
            assert len(group['members']) == 3

            if username == 'owner_user':
                print(data)
                assert data['results']['is_owner'] == True
            else:
                assert data['results']['is_owner'] == False

    @pytest.mark.parametrize('group_name, add_members, group_count', [
        ('Test Group', True, 5),
        ('Test Group', False, 3),
        ('Test Group', False, 10),
        ('Test Group', True, 5),
    ])
    def test_create_group(
        self,
        client,
        auth_data,
        username,
        group_name,
        add_members,
        group_count,
    ):
        user_ids = User.objects.all().values_list('id', flat=True)

        for i in range(group_count):
            data = {
                'name': f"{group_name} {i}",
                'members': user_ids if add_members else [auth_data['user'].id],
                'owner': auth_data['user'].id
            }

            response = client.post(api_url + 'groups/', data, headers={
                'AUTHORIZATION': f"Bearer {auth_data['token']}"
            })

            match username:
                case 'owner_user':
                    if create_groups_count + i >= 8:
                        assert response.status_code == 403
                        assert response.data['results'] == "The limit for creating groups has been reached."
                    else:
                        assert response.status_code == 201
                        assert response.data['result']
                        group = response.data['result']
                        expected_fields = {'id', 'name', 'owner', 'members'}
                        for fields in expected_fields:
                            assert fields in group
                case _:
                    if i >= 8:
                        assert response.status_code == 403
                        assert response.data['results'] == "The limit for creating groups has been reached."
                    else:
                        assert response.status_code == 201
                        created_group = response.data['result']
                        assert created_group
                        assert created_group['owner'] == auth_data['user'].id
                        assert created_group['name'] == data['name']
                        group = response.data['result']
                        expected_fields = {'id', 'name', 'owner', 'members'}
                        for fields in expected_fields:
                            assert fields in group
    
    @pytest.mark.parametrize('is_owner, group_exists', [
        (True, True),
        (True, False),
        (False, True),
        (False, False)
    ])
    def test_delete_group(
            self,
            client,
            username,
            auth_data,
            is_owner,
            group_exists,
    ):
        

        if is_owner:
            group_owner = auth_data['user']
        else:
            owner_user = User.objects.create(username='group_owner')
            group_owner = owner_user

        created_group = Group.objects.create(
            name="Test Group",
            owner=group_owner,
        )

        group_id = created_group.id if group_exists else 9999999999999

        response = client.delete(api_url + f"groups/{group_id}/", headers={
            'AUTHORIZATION': f"Bearer {auth_data['token']}"
        })

        match (is_owner, group_exists):
            case (True, True):
                assert response.status_code == 204
                message = response.data['message']
                assert "success delete group" == message

            case (False, True):
                assert response.status_code == 403
            
            case (True, False):
                assert response.status_code == 404

            case (False, False):
                # First check Group exists
                assert response.status_code == 404


