from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from tinymce.widgets import TinyMCE

from events.models import Event
from .widgets import EventChildrensTreeWidget


class EventForm(forms.ModelForm):
    print_point_1 = forms.CharField(widget=TinyMCE(), required=False)
    print_point_2 = forms.CharField(widget=TinyMCE(), required=False)
    print_point_3 = forms.CharField(widget=TinyMCE(), required=False)
    print_point_4 = forms.CharField(widget=TinyMCE(), required=False)
    print_point_5 = forms.CharField(widget=TinyMCE(), required=False)
    print_point_6 = forms.CharField(widget=TinyMCE(), required=False)
    descendants_tree = forms.CharField(
        widget=EventChildrensTreeWidget(attrs={"class": "show-list-style"}),
        required=False,
        label=_("Descendants tree"),
    )

    class Meta:
        model = Event
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance:
            self.fields["descendants_tree"].initial = instance

    def clean(self):
        if self.is_valid():
            if self.cleaned_data["administrative_units"].count() != 1:
                raise ValidationError(
                    {
                        "administrative_units": _(
                            "You can't select more than one adminstrative_unit."
                        )
                    }
                )
            if (
                self.cleaned_data["basic_purpose"] == "opportunity"
                and not self.cleaned_data["opportunity"]
            ):
                raise ValidationError(
                    {
                        "opportunity": _(
                            "You must select one non-empty opportunity option."
                        )
                    }
                )
            if (
                self.cleaned_data["opportunity"]
                and self.cleaned_data["basic_purpose"] != "opportunity"
            ):
                raise ValidationError(
                    {"basic_purpose": _("You must select 'Opportunity' option.")}
                )


class EventChangeListForm(forms.ModelForm):
    event = forms.ModelMultipleChoiceField(
        queryset=Event.objects.all(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance:
            self.fields["event"].initial = instance.event.all()
