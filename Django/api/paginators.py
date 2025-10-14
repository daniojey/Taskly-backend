
from rest_framework.pagination import PageNumberPagination

class NotificationPaginator(PageNumberPagination):
    page_size = 10  # дефолтное значение элементов на странице
    page_size_query_param = 'page_size'  # параметр для изменения количества элементов