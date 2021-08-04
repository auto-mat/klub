from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = '__all__'

    def clean(self):
        if self.is_valid():
            if self.cleaned_data['administrative_units'].count() != 1:
                raise ValidationError({"administrative_units": _("You can't select more than one adminstrative_unit.")})
            if (self.cleaned_data['basic_purpose'] == "opportunity" and not self.cleaned_data['opportunity']):
                raise ValidationError({"opportunity": _("You must select one non-empty opportunity option.")})
            if self.cleaned_data['opportunity'] and self.cleaned_data['basic_purpose'] != "opportunity":
                raise ValidationError({"basic_purpose": _("You must select 'Opportunity' option.")})
