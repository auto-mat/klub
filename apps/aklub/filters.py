# custom filters

import operator
from datetime import date
from functools import reduce

from django.contrib.admin import SimpleListFilter
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.utils.translation import ugettext as _

from . import models
from .models import Condition, UserProfile


class NullFieldFilter(SimpleListFilter):
    """This fiters nullable fields by
           'All' (no filter),
           'Empty' (field__isnull=True filter)
           'Filled in' (not null).

       Child classes must override the field attribute
       to specify which field this filter should be applied to."""

    field = None

    def lookups(self, request, model_admin):
        return (('filled', _('Filled-in')),
                ('empty', _('Empty')))

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.filter(**{'%s__isnull' % self.field: self.value() == 'empty' and True})


class PaymentsAssignmentsFilter(NullFieldFilter):
    field = 'user'
    title = _("User assignment")
    parameter_name = 'user_assignment'


class UserConditionFilter(SimpleListFilter):
    """Filters using computed dynamic conditions from DB"""

    title = _("Condition")
    parameter_name = 'user_condition'

    def lookups(self, request, model_admin):
        return [(cond.id, cond.name) for cond in Condition.objects.filter(as_filter=True)]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        cond = Condition.objects.filter(id=self.value())[0]

        return models.filter_by_condition(queryset, cond)


class UserConditionFilter1(UserConditionFilter):
    """Filters using computed dynamic conditions from DB"""
    parameter_name = 'user_condition1'


class ActiveCampaignFilter(SimpleListFilter):
    title = u"Active"
    parameter_name = u'active'

    def lookups(self, request, model_admin):
        return (
            ('yes', _(u'Yes')),
            ('no', _(u'No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(Q(terminated__gte=date.today()) | Q(terminated=None), created__lte=date.today())
        if self.value() == 'no':
            return queryset.exclude(Q(terminated__gte=date.today()) | Q(terminated=None), created__lte=date.today())


class EmailFilter(SimpleListFilter):
    title = _(u"Email")
    parameter_name = u'email'

    def lookups(self, request, model_admin):
        return (
            ('duplicate', _(u'Duplicate')),
            ('email-format', _('Not in e-mail format')),
            ('blank', _(u'Blank')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'duplicate':
            duplicates = UserProfile.objects.filter(email__isnull=False).\
                exclude(email__exact='').\
                annotate(email_lower=Lower('email')).\
                values('email_lower').\
                annotate(Count('id')).\
                values('email_lower').\
                order_by().\
                filter(id__count__gt=1).\
                values_list('email', flat=True)
            return queryset.filter(email__in=duplicates)
        if self.value() == 'blank':
            return queryset.filter(Q(email__exact='') or Q(email__isnull=True))
        if self.value() == 'email-format':
            return queryset.exclude(email__iregex=r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+$)")
        return queryset


class TelephoneFilter(SimpleListFilter):
    title = _("Telephone")
    parameter_name = 'telephone'

    def lookups(self, request, model_admin):
        return (
            ('duplicate', _('Duplicate')),
            ('bad-format', _('Not in telephone format')),
            ('blank', _('Blank')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'duplicate':
            duplicates = UserProfile.objects.filter(telephone__isnull=False).\
                exclude(telephone__exact='').\
                values('telephone').\
                annotate(Count('id')).\
                values('telephone').\
                order_by().\
                filter(id__count__gt=1).\
                values_list('telephone', flat=True)
            return queryset.filter(telephone__in=duplicates)
        if self.value() == 'blank':
            return queryset.filter(Q(telephone__exact='') or Q(telephone__isnull=True))
        if self.value() == 'bad-format':
            return queryset.exclude(telephone__iregex=r'^\+?([0-9] *){9,}$').exclude(telephone__exact='').exclude(telephone__isnull=True)
        return queryset


class NameFilter(SimpleListFilter):
    title = _("Name")
    parameter_name = 'name'

    def lookups(self, request, model_admin):
        return (
            ('duplicate', _('Duplicate')),
            ('blank', _('Blank')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'duplicate':
            duplicates = UserProfile.objects.filter(first_name__isnull=False, last_name__isnull=False)
            duplicates = duplicates.exclude(first_name__exact='', last_name__exact='')
            duplicates = duplicates.values('first_name', 'last_name')
            duplicates = duplicates.annotate(Count('id'))
            duplicates = duplicates.values('first_name', 'last_name', 'id')
            duplicates = duplicates.order_by()
            duplicates = duplicates.filter(id__count__gt=1)
            duplicates = duplicates.values_list('first_name', 'last_name')
            print(duplicates)
            query = reduce(
                operator.or_,
                (Q(first_name=fn, last_name=ln) for fn, ln in duplicates),
            )
            return queryset.filter(query)
        if self.value() == 'blank':
            return queryset.filter(
                (Q(first_name__exact='') or Q(first_name__isnull=True)) and
                (Q(last_name__exact='') or Q(last_name__isnull=True)),
            )
        return queryset
