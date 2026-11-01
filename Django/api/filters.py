import django_filters


class SessionsFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    user = django_filters.CharFilter(field_name="performer__username", lookup_expr="icontains")