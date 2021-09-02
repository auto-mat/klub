from django import forms

from .models import Interaction


class InteractionInlineForm(forms.ModelForm):
    class Meta:
        model = Interaction
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.request.user.has_perm("aklub.can_edit_all_units"):
            if not self.instance.pk:
                self.fields[
                    "administrative_unit"
                ].queryset = self.request.user.administrated_units
                self.fields["administrative_unit"].empty_label = None
            else:
                if (
                    self.request.user.administrated_units.first()
                    != self.instance.administrative_unit
                ):
                    for field_name in self.fields:
                        self.fields[field_name].disabled = True
                else:
                    self.fields[
                        "administrative_unit"
                    ].queryset = self.request.user.administrated_units
                    self.fields["administrative_unit"].empty_label = None


class InteractionInlineFormset(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = kwargs["instance"]
        qs = Interaction.objects.filter(
            user=user, communication_type__in=("individual", "auto")
        ).order_by("-date_from")[:10]
        qs = qs.select_related("created_by", "handled_by")
        self.queryset = qs
