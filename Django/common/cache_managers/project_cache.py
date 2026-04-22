from django.core.cache import cache


class ProjectCacheManager:

    def clear_list_cache(filters, user_id):
        pass

    def clear_all_cache(user_id):
        pattern = f'projects_list_{user_id}'

        cache.delete(pattern)