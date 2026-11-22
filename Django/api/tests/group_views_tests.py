from django.db.utils import IntegrityError
from django.utils import timezone
from django.utils.timezone import timedelta
import pytest

from users.models import Group, Notification, User
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


@pytest.mark.django_db
class TestListGroup:
    url_string = 'api:groups-list'
    list_url = get_url('api:groups-list')

    @pytest.mark.parametrize('groups_count, members_count', [
        pytest.param(0, 0),
        pytest.param(4, 0),
        pytest.param(5, 5),
        pytest.param(10, 3),
    ])
    def test_get_group_list(
        self, 
        auth_api_client, 
        groups, 
        user,
        users,
        groups_count,
        members_count,
    ):
        users = users.create_batch(members_count)

        if members_count > 0:
            groups.create_batch(groups_count, members=(*users,), owner=user)
        else:
            groups.create_batch(groups_count, owner=user)

        response = auth_api_client.get(self.list_url)

        assert response.status_code == 200, response.data

        data = response.data['results']
        assert len(data) == groups_count, response

        members_and_owner = members_count + 1
        for g in data:
            assert g['count_members'] == members_and_owner, g['count_members']

    @pytest.mark.parametrize('groups_count', [0, 1, 3])
    def test_get_list_not_member(self,auth_api_client, groups, groups_count):
        groups.create_batch(groups_count)

        response = auth_api_client.get(self.list_url)

        assert response.status_code, response
        assert len(response.data['results']) == 0

    def test_not_auth_user(self, api_client):
        response = api_client.get(self.list_url)

        assert response.status_code == 401

        
    @pytest.mark.parametrize('filter_name, g_string, group_param', [
        pytest.param('Name', 'A-z', 'Agroup', id="filter group name"),
        pytest.param('Name reverse', 'Z-a', 'Zgroup', id="filter group name reverse"),
        pytest.param('Created_date', 'created', timezone.now() + timedelta(days=1), id="filter date created"),
        pytest.param('Created_date reverse', '', timezone.now() - timedelta(days=1))
    ])
    def test_filter_list(
        self, 
        auth_api_client, 
        user, 
        users, 
        groups,
        filter_name,
        g_string,
        group_param
    ):
        users = users.create_batch(2)
        groups.create_batch(5, members=(*users,), owner=user)

        match (filter_name):
            case 'Name':
                g = groups.create(name=group_param, owner=user)
            case 'Name reverse':
                g = groups.create(name=group_param, owner=user)
            case 'Created_date':
                g = groups.create(created_at=group_param, owner=user)
            case 'Created_date reverse':
                g = groups.create(created_at=group_param, owner=user)

        response = auth_api_client.get(self.list_url, data={'f': g_string})

        assert response.status_code == 200

        data = response.data['results']


        match (filter_name):
            case 'Name':
                assert data[0]['id'] == g.id,data
            case 'Name reverse':
                assert data[0]['id'] == g.id, data
            case 'Created_date':
                assert data[0]['id'] == g.id, data
            case 'Created_date reverse':
                assert data[-1]['id'] == g.id, data


@pytest.mark.django_db
class TestRetrieveGroup:
    retrieve_url = staticmethod(
        lambda pk: get_url('api:groups-detail', pk=pk)
    )

    @pytest.mark.parametrize('user_type', ['owner','member'])
    def test_get_group(
            self,  
            auth_api_client,
            auth_client_for,
            custom_user, 
            groups,
            user,
            user_type,
        ):

        match (user_type):
            case 'owner':
                group = groups.create(owner=user)

                response = auth_api_client.get(self.retrieve_url(group.id))
                assert response.status_code == 200, response
                data = response.data['results']
                assert user.id in [m['id'] for m in data['members']], response.data
                assert data['is_owner'] == True
            case 'member':
                new_member = custom_user(username="best user")
                group = groups.create(owner=user, members=(new_member,))

                new_api_client = auth_client_for(new_member)

                response = new_api_client.get(self.retrieve_url(group.id))

                assert response.status_code == 200

                data = response.data['results']

                assert data, response
                assert data['id'] == group.id, response.data
                assert new_member.id in [m['id'] for m in data['members']], response.data
                assert data['is_owner'] == False, response.data


    def test_anonymous_user(self, api_client, groups):
        group = groups.create()
        response = api_client.get(self.retrieve_url(group.id))

        assert response.status_code == 401


    def test_without_group(self, auth_api_client):
        response = auth_api_client.get(self.retrieve_url(999999999999999))

        assert response.status_code == 404



@pytest.mark.django_db
class TestGroupDelete:
    delete_url = staticmethod(
        lambda pk: get_url('api:groups-detail', pk=pk)
    )

    @pytest.mark.parametrize('user_type, status', [
        pytest.param('owner', 204),
        pytest.param('member', 403),
        pytest.param('another user', 403)
    ])
    def test_delete_group(
        self, 
        auth_api_client, 
        auth_client_for,
        groups, 
        user, 
        users,
        user_type, 
        status
    ):
        new_user = users.create(username="test two user")

        if user_type == 'another user':
            group = groups.create(owner=user)
        else:
            group = groups.create(owner=user, members=(new_user,))

        
        if user_type != 'owner':
            new_client = auth_client_for(new_user)
            response = new_client.delete(self.delete_url(group.id))
        else:
            response = auth_api_client.delete(self.delete_url(group.id))

        match (user_type):
            case 'owner':
                assert response.status_code == status, response

                assert not Group.objects.filter(id=group.id).exists()
            case 'member' | 'another user':
                assert response.status_code == status


@pytest.mark.django_db
class TestGroupUserInvite:
    created_url = staticmethod(
        lambda pk: get_url(f"api:groups-user-invite-group", pk=pk)
    )


    def test_add_user(
            self, 
            auth_api_client, 
            user, 
            group, 
            users,
            mocker
        ):

        mocker.patch("api.tasks.async_to_sync")

        new_member = users.create(username="new member")

        members = list(group.members.all())
        assert user.id in [m.id for m in members]
        assert not new_member.id in [m.id for m in members]

        response = auth_api_client.post(self.created_url(group.id), data={'user_id': new_member.id}, format='json')

        assert response.status_code == 200, response.data

        notify = Notification.objects.filter(
            user_id=new_member.id, 
            data__group_id=group.id,
            notify_type=Notification.INVITE_MESSAGE
        ).first()

        assert notify
        assert timezone.localtime(notify.created_at).date() == timezone.localtime(timezone.now()).date()

    @pytest.mark.parametrize('user_id, status, expected_error,', [
        pytest.param(9999999999999, 404, None, id="expected_user_not_found"),
        pytest.param('lol', None, ValueError, id="Expected value error because 'lol' != pk"),
        pytest.param(None, None, TypeError, id="Expected type error because None db cant use for search"),
    ])
    def test_user_id_not_found(
            self,
            auth_api_client,
            users,
            group,
            user,
            user_id,
            status,
            expected_error
    ):
        new_member = users.create()
        assert not new_member.id in [m.id for m in group.members.all()]

        if expected_error:
            with pytest.raises(expected_error):
                response = auth_api_client.post(self.created_url(group.pk), data={'user_id': user_id})
        else:
            response = auth_api_client.post(self.created_url(group.pk), data={'user_id': user_id})
            assert response.status_code == status
            

    def test_no_owner_group(
            self,
            users,
            auth_client_for,
            group,
            user,
    ):
        assert group.owner_id == user.id
        
        new_user = users.create(username='Noowner')
        another_user = users.create(username='another user')

        api_client = auth_client_for(new_user)

        response = api_client.post(self.created_url(group.id), data={'user_id': another_user.id})

        assert response.status_code == 403

    def test_not_authenticate_user(
            self,
            api_client,
            group,
            user
    ):
        response = api_client.post(self.created_url(group.id), data={'user_id': user.id})

        assert response.status_code == 401

    def test_owner_cant_add_himself(
            self,
            auth_api_client,
            user,
            group,
    ):
        assert user.id == group.owner_id

        response = auth_api_client.post(self.created_url(group.id), data={'user_id': user.id})

        assert response.status_code == 400, response.data

@pytest.mark.django_db
class TestGroupProcessInvite:
    invite_url = staticmethod(
        lambda pk: get_url('api:groups-processing-group-invite', pk=pk)
    )

    def test_process_invite(
            self,
            group,
            users,
            auth_client_for,
            user,
            notification
    ):
        new_user = users.create(username="new member")
        invite_notify = notification(user=new_user, group_id=group.id)


        invite_data = {
            'type':'accept',
            'notify': {
                'id': invite_notify.id, 
                'user': {
                    'id': new_user.id,
                    'username': new_user.username
                }
            }
        }
        

        api_client = auth_client_for(new_user)
        response = api_client.post(self.invite_url(group.id), data=invite_data, format='json')

        assert response.status_code == 200, response.data
        assert new_user.id in [m.id for m in group.members.all()]
        assert not Notification.objects.filter(id=invite_notify.id).exists()


    @pytest.mark.parametrize('excluded, status, error', [
        pytest.param('type', 400, None),
        pytest.param('notify', 400, AttributeError),
        pytest.param('notify_id', 404, None),
        pytest.param('user', None, AttributeError),
        pytest.param('type, user', 400, None),
        pytest.param('notify_id, type', 404, None)
    ])
    def test_invalid_response(
            self,
            auth_client_for,
            user,
            users,
            group,
            notify_invalid_data,
            notification,
            excluded,
            status,
            error
    ):
        new_user = users.create(username='testUser')
        new_notify = notification(new_user, group_id=group.id)
        data = notify_invalid_data(new_user, new_notify, excluded)

        api_client = auth_client_for(new_user)

        if error:
            with pytest.raises(error):
                response = api_client.post(self.invite_url(group.id), data=data, format='json')

        else:
            response = api_client.post(self.invite_url(group.id), data=data, format='json')
            assert response.status_code == status, response.data


    def test_no_authenticate(self, api_client, group):
        response = api_client.post(self.invite_url(group.id), data={})

        assert response.status_code == 401