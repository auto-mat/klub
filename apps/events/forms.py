from django import forms
from django.core.exceptions import ValidationError

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = '__all__'

    def clean(self):
        if self.is_valid():
            if self.cleaned_data['administrative_units'].count() != 1:
                raise ValidationError({"administrative_units": "you can't select more than one adminstrative_unit"})
