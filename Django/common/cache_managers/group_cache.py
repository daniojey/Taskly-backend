

from django.core.cache import cache


class GroupCacheManager:

    def clean_group_list_cache(filters, user_id: int):
        pipe = cache
        
        patterns = [
            f"groups_filter_{_filter}_user_{user_id}"
            for _filter in filters
        ]

        for pattern in patterns:
            pipe.delete(pattern)