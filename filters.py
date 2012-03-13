# custom filters

from django.utils.translation import ugettext as _
from django.contrib.admin import SimpleListFilter
from django.db.models import Sum, Count

from models import Condition, User
import autocom

class NullFieldFilter(SimpleListFilter):
    """This fiters nullable fields by 
           'All' (no filter),
           'Empty' (field__isnull=True filter)
           'Filled in' (not null).

       Child classes must override the field attribute
       to specify which field this filter should be applied to."""

    field=None

    def lookups(self, request, model_admin):
        return (('filled', _('Filled-in')),
                ('empty', _('Empty')))

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.filter(**{'%s__isnull' % self.field: self.value()=='empty' and True})

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
        # Hack: It would be better to work directly on the objects
        # of the queryset rather than extracting ids from another
        # DB query and then filtering the former queryset
        all_users = User.objects.all().annotate(**User.annotations)
        filtered_ids = [user.id for user in all_users
                        if cond.is_true(user)]
        return queryset.filter(id__in=filtered_ids)
