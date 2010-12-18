# custom filters

from django.utils.translation import ugettext as _
from django.contrib.admin.filterspecs import FilterSpec, RelatedFilterSpec

from models import Condition, User
import autocom

class NullFilterSpec(RelatedFilterSpec):
    """This fiters nullable related fields by 
           'All' (no filter),
           'Empty' (field__isnull=True filter)
           'Filled in' (not null).
       You need to register the filter for each model you want to apply it to."""
    def __init__(self, f, request, params, model, model_admin):
        super(NullFilterSpec, self).__init__(f, request, params, model, model_admin)
        self.lookup_kwarg = '%s__isnull' % f.name
        self.lookup_val = request.GET.get(self.lookup_kwarg, None)
    
    def choices(self, cl):
        for k, v in ((_('All'), None), (_('Filled-in'), ''), (_('Empty'), '1')):
            yield {
                'selected' : self.lookup_val == v,
                'query_string' : cl.get_query_string({self.lookup_kwarg : v}),
                'display' : k
            }

class ConditionFilterSpec(FilterSpec):
    """Filters using computed dynamic conditions from DB"""
    def __init__(self, f, request, params, model, model_admin):
        super(ConditionFilterSpec, self).__init__(f, request, params, model,
                                                  model_admin)
        self.lookup_kwarg = 'id__in'
        self.lookup_val = request.GET.get(self.lookup_kwarg, None)

    def choices(self, cl):
        choices = [(_("All"), 0, None)]
        for cond in Condition.objects.all():
            choices += [(cond.name, cond.id,
                         # Hack: This is gross, we are going to
                         # compute results of many filters that might
                         # not be even used
                         [user.id for user in User.objects.all()
                          if cond.is_true(user)])]
        for k, v, ids in choices:
            query = {}
            if ids:
                query[self.lookup_kwarg] = ",".join(map(str,ids))
            yield {
                'query_string' : cl.get_query_string(query),
                'display' : k
            }    

# Insert the filter before any other filter. Otherwise admin would apply the default filter
# for ForeignKey which is the RelatedFilterSpec (the one that lists all values as filters) 
# Note by HH: How does the bellow work is a mystery to me...
RelatedFilterSpec.filter_specs.insert(0, (lambda f: f.null, NullFilterSpec))
# Hack: This will match the firstname column in any model that contains it...
FilterSpec.filter_specs.insert(0, (lambda f: bool(f.name=='firstname'),
                                   ConditionFilterSpec))

# THIS DOESN'T WORK YET
class ActionFilterSpec(FilterSpec):
        def __init__(self, f, request, params, model, model_admin):
                super(ActionFilterSpec, self).__init__(request, params, model, model_admin, f)
                self.lookup_kwarg = 'communication__isnull'
                self.lookup_val = request.GET.get(self.lookup_kwarg, None)
                self.lookup_choices = []
                self.lookup_choices.append(('', _('Action required')))
                #self.lookup_choices.append((False, u'Not needed')) # doesn't work in Django 1.1.1
        def title(self):
                return u'Action required'
        def has_output(self):
                return True
        def consumed_params(self):
                return [self.lookup_kwarg]
#FilterSpec.filter_specs.insert(0, (lambda f: f.null, ActionFilterSpec))
