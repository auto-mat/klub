# -*- coding: utf-8 -*-
import datetime

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UserChangeForm, UserCreationForm, UsernameField
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import IntegrityError, transaction
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from smmapdfs.models import PdfSandwichType

from .models import AdministrativeUnit, CompanyContact, Event, ProfileEmail, Telephone

Profile = get_user_model()


class TaxConfirmationForm(forms.Form):
    year = forms.IntegerField(label=_('Year'))

    def __init__(self, *args, **kwargs):
        profiles = kwargs.pop('profiles', None)
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        self.fields['year'].initial = datetime.datetime.now().year - 1
        self.fields['year'].required = True
        if not profiles:
            profiles = Profile.objects.none()
        self.fields['profile'] = forms.ModelMultipleChoiceField(queryset=profiles, widget=FilteredSelectMultiple("UserProfile", False))
        self.fields['profile'].initial = profiles

        if profiles:
            if profiles.first().polymorphic_ctype.model == 'userprofile':
                profile_type = 'user_profile'
            else:
                profile_type = 'company_profile'

            if not request.user.has_perm('aklub.can_edit_all_units'):
                au = request.user.administrated_units.all()
            else:
                au = AdministrativeUnit.objects.all()

            pdf_type_queryset = PdfSandwichType.objects.filter(
                                            pdfsandwichtypeconnector__administrative_unit__in=au,
                                            pdfsandwichtypeconnector__profile_type=profile_type,
                                            )
            self.fields['pdf_type'] = forms.ModelChoiceField(queryset=pdf_type_queryset)
            self.fields['pdf_type'].required = True


def hidden_fields_switcher(self):
    for field in self.fields:
        if field not in self.non_hidden_fields:
            self.fields[field].widget = forms.HiddenInput()
    return self


class UserCreateForm(UserCreationForm):
    password = ReadOnlyPasswordHashField()
    hidden_lock_change = forms.CharField(widget=forms.HiddenInput(), initial='locked', required=False)
    telephone = forms.CharField(
        required=False,
        validators=[
            RegexValidator(
                r'^\+?(42(0|1){1})?\s?\d{3}\s?\d{3}\s?\d{3}$',
                _("Telephone must consist of numbers, spaces and + sign or maximum number count is higher."),
            ),
        ],
    )

    class Meta:
        model = Profile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.non_hidden_fields = ('email', 'administrative_units', 'groups', 'is_superuser', 'administrated_units', 'is_staff')
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['username'].required = False
        self.fields['password'].help_text = 'You can set password in the next step or anytime in user detail form'
        self.fields['administrative_units'].required = True

        if self.request.method == 'GET':
            hidden_fields_switcher(self)

    def clean(self, *args, **kwargs):
        if self._errors and self.data.get('hidden_lock_change') == 'locked':
            hidden_fields_switcher(self)
        return super().clean()

    def is_valid(self):
        # validation change "locked" and "unlocked" field , which helps to make double form
        if self.data.get('hidden_lock_change') == 'locked' and super().is_valid():
            self.data = self.data.copy()
            self.data['hidden_lock_change'] = 'unlocked'
            return False
        return super().is_valid()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['username']
        email = user.email
        user.email = None
        user.save()
        if self.cleaned_data['email'] is not None:
            ProfileEmail.objects.create(email=email, user=user, is_primary=True)
        if self.cleaned_data['telephone']:
            Telephone.objects.create(telephone=self.cleaned_data['telephone'], user=user, is_primary=True)
        return user


class UserUpdateForm(UserChangeForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Profile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['password'].help_text = (
            "Raw passwords are not stored, so there is no way to see "
            "this user's password, but you can <a href=\"%s\"> "
            "<strong>Change the Password</strong> using this form</a>."
                                            ) % reverse_lazy(
            'admin:auth_user_password_change',
            args=[self.instance.id],
        )

    def save(self, commit=True):
        user = super(UserChangeForm, self).save(commit=False)
        user.username = self.cleaned_data['username']

        if commit:
            user.save()
        return user


class UnitUserProfileAddForm(forms.ModelForm):
    username = forms.CharField(required=False)
    hidden_lock_change = forms.CharField(widget=forms.HiddenInput(), initial='locked', required=False)
    telephone = forms.CharField(
        required=False,
        validators=[
            RegexValidator(
                r'^\+?(42(0|1){1})?\s?\d{3}\s?\d{3}\s?\d{3}$',
                _("Telephone must consist of numbers, spaces and + sign or maximum number count is higher."),
            ),
        ],
    )

    class Meta:
        model = Profile
        fields = (
            'username',
            # 'first_name',
            # 'last_name',
            # 'title_before',
            # 'title_after',
            'email',
            # 'useprofile__sex',
            # 'birth_day',
            # 'birth_month',
            # 'age_group',
            'note',
            'administrative_units',
            'street',
            'city',
            'country',
            'zip_code',
            'different_correspondence_address',
            'correspondence_street',
            'correspondence_city',
            'correspondence_country',
            'correspondence_zip_code',
            'addressment',
            'addressment_on_envelope',
        )
        field_classes = {'username': UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.non_hidden_fields = ('email', 'administrative_units')
        self.fields['administrative_units'].queryset = self.request.user.administrated_units.all()
        self.fields['administrative_units'].required = True

        if self.request.method == 'GET':
            hidden_fields_switcher(self)

    def clean(self):
        if self._errors and self.data.get('hidden_lock_change') == 'locked':
            hidden_fields_switcher(self)
        return super().clean()

    def is_valid(self):
        if self.data.get('hidden_lock_change') == 'locked' and super().is_valid():
            self.data = self.data.copy()
            self.data['hidden_lock_change'] = 'unlocked'
            return False
        return super().is_valid()

    def save(self, commit=True):
        user = super().save(commit=False)
        email = user.email
        user.email = None
        user.save()
        if self.cleaned_data['email'] is not None:
            ProfileEmail.objects.create(email=email, user=user, is_primary=True)
        if self.cleaned_data['telephone']:
            Telephone.objects.create(telephone=self.cleaned_data['telephone'], user=user, is_primary=True)
        return user


class UnitUserProfileChangeForm(UnitUserProfileAddForm):

    class Meta(UnitUserProfileAddForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super(UnitUserProfileAddForm, self).__init__(*args, **kwargs)
        self.fields['administrative_units'].queryset = self.instance.administrative_units.all()
        self.fields['administrative_units'].disabled = True

    def clean(self):
        # we pop all fields which we dont want to be changed (administated things)
        ignore_fields = ['is_superuser', 'user_permissions', 'is_staff', 'password', 'administrated_units', 'groups']
        keys = list(self.cleaned_data)
        [self.cleaned_data.pop(field) for field in keys if field in ignore_fields]
        return super(UnitUserProfileAddForm, self).clean()

    def is_valid(self):
        return super(UnitUserProfileAddForm, self).is_valid()


class CompanyProfileAddForm(forms.ModelForm):
    no_crn_check = forms.BooleanField(
                label=_("No crm check"),
                required=False,
                initial=False,
    )
    hidden_lock_change = forms.CharField(widget=forms.HiddenInput(), initial='locked', required=False)
    telephone = forms.CharField(
        required=False,
        validators=[
            RegexValidator(
                r'^\+?(42(0|1){1})?\s?\d{3}\s?\d{3}\s?\d{3}$',
                _("Telephone must consist of numbers, spaces and + sign or maximum number count is higher."),
            ),
        ],
    )
    contact_first_name = forms.CharField(required=False, max_length=256)
    contact_last_name = forms.CharField(required=False, max_length=256)

    class Meta:
        model = Profile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.non_hidden_fields = ('crn', 'tin', 'no_crn_check', 'administrative_units')
        if not self.request.user.has_perm('aklub.can_edit_all_units'):
            self.fields['administrative_units'].queryset = self.request.user.administrated_units.all()
        self.fields['administrative_units'].required = True
        if self.request.method == 'GET':
            hidden_fields_switcher(self)

    def clean(self):
        if self.cleaned_data.get('crn') is None and self.cleaned_data.get('no_crn_check') is False:
            self.add_error('no_crn_check', _('Please confirm empty crn number'))

        if self._errors and self.data.get('hidden_lock_change') == 'locked':
            hidden_fields_switcher(self)
            return super().clean()

        return super().clean()

    def is_valid(self):
        if self.data.get('hidden_lock_change') == 'locked' and super().is_valid():
            self.data = self.data.copy()
            self.data['hidden_lock_change'] = 'unlocked'
            return False
        return super().is_valid()

    def save(self, commit=True):
        user = super().save(commit=False)
        email = user.email
        user.email = None
        user.save()
        if email or self.cleaned_data['telephone'] or self.cleaned_data['contact_first_name'] or self.cleaned_data['contact_last_name']:
            for unit in self.cleaned_data['administrative_units']:
                contact = CompanyContact.objects.create(
                    email=email,
                    telephone=self.cleaned_data['telephone'],
                    company=user,
                    administrative_unit=unit,
                    contact_first_name=self.cleaned_data['contact_first_name'],
                    contact_last_name=self.cleaned_data['contact_last_name'],
                )
                try:
                    contact.is_primary = True
                    with transaction.atomic():
                        contact.save()
                except IntegrityError:
                    pass
        return user


class CompanyProfileChangeForm(CompanyProfileAddForm):
    class Meta(CompanyProfileAddForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super(CompanyProfileAddForm, self).__init__(*args, **kwargs)
        if not self.request.user.has_perm('aklub.can_edit_all_units'):
            self.fields['administrative_units'].queryset = self.instance.administrative_units.all()
            self.fields['administrative_units'].disabled = True

    def clean(self):
        return super(CompanyProfileAddForm, self).clean()

    def is_valid(self):
        return super(CompanyProfileAddForm, self).is_valid()


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = '__all__'

    def clean(self):
        if self.is_valid():
            if self.cleaned_data['administrative_units'].count() != 1:
                raise ValidationError({"administrative_units": "you can't select more than one adminstrative_unit"})
