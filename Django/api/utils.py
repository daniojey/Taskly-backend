



class GroupLogger():

    @classmethod
    def _create_log(cls, group, event, event_type, anchor=None, **detail):
        from users.models import GroupLogs

        return GroupLogs.objects.create(
            group=group,
            event=event,
            event_type=event_type,
            anchor=anchor,
            data=detail
        )
    
    @classmethod
    def add_member(cls, group, event_type, invited_user):
        detail = {'invited_user': invited_user.username }
        
        return cls._create_log(
            group=group,
            event=f"Add {invited_user.username} in group",
            event_type=event_type,
            detail=detail
        )
    
    @classmethod
    def kick_member(cls, group, event_type, kicked_user, triggered_user):
        detail = {'kicked_user': kicked_user.username}

        return cls._create_log(
            group=group,
            event=f'kick user: {kicked_user}',
            event_type=event_type,
            anchor=triggered_user,
            detail=detail
        )
    
    @classmethod
    def send_invite_member(cls, group, event_type, target_user, triggered_user):

        return cls._create_log(
            group=group,
            event=f"{triggered_user.username} sent an invitation to the group to user {target_user.username}",
            event_type=event_type,
            anchor=triggered_user,
        )
    
    @classmethod
    def invite_deflected(cls, group, event_type, target_user):

        return cls._create_log(
            group=group,
            event=f"{target_user} declined the invitation",
            event_type=event_type,
        )