from rest_framework.pagination import LimitOffsetPagination

class RecipePagination(LimitOffsetPagination):
    default_limit = 25
    max_limit = 100