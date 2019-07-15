# custom filters

import operator
from datetime import date, timedelta
from functools import reduce

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.filters import RelatedFieldListFilter
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.utils.translation import ugettext as _

from . import models
from .models import Condition, Telephone, UserProfile


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
    field = 'user_donor_payment_channel'
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
        return queryset


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
                values_list('email_lower', flat=True)
            return queryset.annotate(email_lower=Lower('email')).filter(email_lower__in=duplicates)
        if self.value() == 'blank':
            return queryset.filter(Q(email__exact='') or Q(email__isnull=True))
        if self.value() == 'email-format':
            return queryset.exclude(email__iregex=r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+$)")
        return queryset


class RegularPaymentsFilter(SimpleListFilter):
    title = _("Regular payments (of any user in campaign)")
    parameter_name = 'regular_payments'

    def lookups(self, request, model_admin):
        return (
            ('not-delayed', _('Not dealyed')),
            ('delayed', _('Delayed or none')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'not-delayed':
            return UserProfile.objects.filter(
                userchannels__expected_regular_payment_date__gt=date.today() - timedelta(days=11),
            )
        if self.value() == 'delayed':
            return UserProfile.objects.exclude(
                userchannels__expected_regular_payment_date__gt=date.today() - timedelta(days=11),
            )
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
            duplicates = Telephone.objects.filter(telephone__isnull=False).\
                exclude(telephone__exact='').\
                values('telephone').\
                annotate(Count('id')).\
                values('telephone').\
                order_by().\
                filter(id__count__gt=1).\
                values_list('telephone', flat=True)
            return queryset.filter(telephone__telephone__in=duplicates)
        if self.value() == 'blank':
            return queryset.filter(Q(telephone__telephone__exact='') | Q(telephone__telephone__isnull=True) | Q(telephone__isnull=True))
        if self.value() == 'bad-format':
            return queryset.exclude(
                telephone__telephone__iregex=r'^\+?([0-9] *){9,}$',
                telephone__telephone__exact='',
                telephone__telephone__isnull=True,
            )
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


class UnitFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        return field.get_choices(include_blank=False, limit_choices_to={'pk__in': request.user.administrated_units.all()})


class AdministrativeUnitAdminMixin(object):
    queryset_unit_param = 'administrative_units'

    def get_queryset(self, request):
        queryset = super(admin.ModelAdmin, self).get_queryset(request)
        if request.user.has_perm('aklub.can_edit_all_units'):
            return queryset
        kwargs = {self.queryset_unit_param + '__in': request.user.administrated_units.all()}
        return queryset.filter(**kwargs).distinct()  # The distinct is necessarry here for unit admins, that have more cities

    def lookup_allowed(self, key, value):
        allowed_lookups = (
            self.queryset_unit_param,
            self.queryset_unit_param + "__id__exact",
            self.queryset_unit_param + "__isnull",
        )
        if key in allowed_lookups:
            return True
        return super().lookup_allowed(key, value)

    def get_list_filter(self, request):
        list_filter = ((self.queryset_unit_param, UnitFilter),) + tuple(super().get_list_filter(request))
        return list_filter


def unit_admin_mixin_generator(queryset_unit):
    class AUAMixin(AdministrativeUnitAdminMixin):
        queryset_unit_param = queryset_unit
    return AUAMixin
