



class GroupLogger():

    @classmethod
    def _create_log(cls, group, event, event_type, anchor, **detail):
        from Django.users.models import GroupLogs

        return GroupLogs.objects.create(
            group=group,
            event=event,
            event_type=event_type,
            anchor=anchor,
            data=detail
        )
    
    @classmethod
    def add_member(cls, group, event_type, invited_user, triggered_user):
        detail = {'invited_user': invited_user.username }
        
        return cls._create_log(
            group=group,
            event=f"{triggered_user} invite {invited_user}",
            event_type=event_type,
            anchor=triggered_user,
            detail=detail
        )