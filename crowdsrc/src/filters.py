import operator
from functools import reduce

# Crowdsrc imports
from crowdsrc.src.models import User

# Django imports
from django.utils import six
from django.db.models import Q
from rest_framework.filters import SearchFilter


# Custom search filter for users that respects user privacy settings
# and only returns users by fields that they have approved for searching
class UserSearchFilter(SearchFilter):
    def filter_queryset(self, request, queryset, view):
        queryset = User.objects.all().order_by(
            'username')  # Force queryset to be user objects

        search_fields = ('username', 'email', 'first_name',
                         'last_name', 'profile__location')
        search_terms = self.get_search_terms(request)

        if not search_terms:
            return queryset

        base = queryset
        conditions = []  # Create search conditions that respect user privacy settings
        for search_term in search_terms:
            queries = [
                Q(settings__privacy__allow_email_search=True,
                  email__icontains=search_term),
                Q(settings__privacy__allow_loc_search=True,
                  profile__location__icontains=search_term),
                Q(settings__privacy__allow_username_search=True,
                  username__icontains=search_term),
                Q(settings__privacy__allow_name_search=True,
                  first_name__icontains=search_term),
                Q(settings__privacy__allow_name_search=True,
                  last_name__icontains=search_term)
            ]
            conditions.append(reduce(operator.or_, queries))
        queryset = queryset.filter(reduce(operator.and_, conditions))

        # only call distinct if absolutely necessary to save
        # computational overhead
        if self.must_call_distinct(queryset, search_fields):
            queryset = distinct(queryset, base)

        return queryset
