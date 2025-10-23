
from rest_framework.pagination import PageNumberPagination, CursorPagination

from rest_framework.response import Response

class NotificationPaginator(PageNumberPagination):
    page_size = 5  # дефолтное значение элементов на странице
    page_size_query_param = 'page_size'  # параметр для изменения количества элементов  

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'items_per_page': self.page_size,
            'results': data,
        })
    

class ChatMessagePaginator(CursorPagination):
    page_size = 9
    ordering = '-id'
    max_page_size= 40