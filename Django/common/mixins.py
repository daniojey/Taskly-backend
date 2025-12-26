from django.core.cache import cache
from django.db.models import QuerySet

class CacheMixin:
    def set_get_cache(self, query: QuerySet, key_cache: str, cache_time: int = 60):
        data = cache.get(key_cache)
        print(data, 'GET CACHE')

        if not data:
            data = query
            cache.set(key_cache, data, cache_time)
            return data
        print(data, 'DATAS GETS')
        return data
    
    def set_cache(self, query: QuerySet, key_cache: str, cache_time: int = 60):
        data = query
        cache.set(key_cache, data, cache_time)
        return data
    
    def get_cache(self, key_cache: str):
        data = cache.get(key_cache)

        if not data:
            return None
        else:
            return data