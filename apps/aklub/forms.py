# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UserChangeForm, UserCreationForm, UsernameField
from django.core.exceptions import ValidationError
from django.shortcuts import reverse
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import CompanyProfile, ProfileEmail, Telephone
from .views import get_unique_username

Profile = get_user_model()


def username_validation(user, fields):
    if user.username == '':
        user.username = get_unique_username(fields['email'])
    else:
        user.username = fields['username']


def hidden_fields_switcher(self):
    for field in self.fields:
        if field not in self.non_hidden_fields:
            self.fields[field].widget = forms.HiddenInput()
    return self


class UserCreateForm(UserCreationForm):
    password = ReadOnlyPasswordHashField()
    hidden_lock_change = forms.CharField(widget=forms.HiddenInput(), initial='locked', required=False)
    telephone = forms.CharField(required=False)

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

        if self.request.method == 'GET':
            hidden_fields_switcher(self)

    def clean(self, *args, **kwargs):
        if self._errors:
            hidden_fields_switcher(self)
            return super().clean()

        if self.cleaned_data.get('email') is not None:
            try:
                email = ProfileEmail.objects.get(email=self.cleaned_data['email'])
                url = reverse('admin:aklub_userprofile_change', args=(email.user.pk,))
                self.add_error(
                    'email',
                    mark_safe(
                        _(f'<a href="{url}">User with this email already exist in database, click here to edit</a>'),
                    ),
                )
                hidden_fields_switcher(self)
                return super().clean()
            except ProfileEmail.DoesNotExist:
                pass
        if self.cleaned_data['hidden_lock_change'] == 'locked':
            self.data = self.data.copy()
            self.data['hidden_lock_change'] = 'unlocked'
            raise ValidationError('Email is not used in database')

        return super().clean()

    def save(self, commit=True):
        user = super().save(commit=False)

        user.username = self.cleaned_data['username']
        username_validation(user=user, fields=self.cleaned_data)
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
        username_validation(user=user, fields=self.cleaned_data)

        if commit:
            user.save()
        return user


class UnitUserProfileAddForm(forms.ModelForm):
    username = forms.CharField(required=False)
    hidden_lock_change = forms.CharField(widget=forms.HiddenInput(), initial='locked', required=False)
    telephone = forms.CharField(required=False)

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
        if self._errors:
            hidden_fields_switcher(self)
            return super().clean()

        if self.cleaned_data.get('email') is not None:
            try:
                email = ProfileEmail.objects.get(email=self.cleaned_data['email'])
                user = email.user
                user.administrative_units.add(self.request.user.administrated_units.first())
                url = reverse('admin:aklub_userprofile_change', args=(user.pk,))
                self.add_error(
                    'email',
                    mark_safe(
                        _(f'<a href="{url}">User with this email already exist in database and is available now, click here to edit</a>'),
                    ),
                )
                hidden_fields_switcher(self)
                return super().clean()
            except ProfileEmail.DoesNotExist:
                pass
        if self.cleaned_data['hidden_lock_change'] == 'locked':
            self.data = self.data.copy()
            self.data['hidden_lock_change'] = 'unlocked'
            raise ValidationError('Email is not used in database')

        return super().clean()

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
        pass


class CompanyProfileAddForm(forms.ModelForm):
    no_crn_check = forms.BooleanField(
                required=False,
                initial=False,
    )
    hidden_lock_change = forms.CharField(widget=forms.HiddenInput(), initial='locked', required=False)
    telephone = forms.CharField(required=False)

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

    def clean(self): # noqa
        if self._errors:
            hidden_fields_switcher(self)
            return super().clean()

        if self.cleaned_data.get('crn') is None and self.cleaned_data.get('no_crn_check') is False:
            self.add_error('no_crn_check', 'Please confirm empty crn number')
            hidden_fields_switcher(self)

        elif self.cleaned_data.get('crn') is not None and self.cleaned_data.get('no_crn_check') is True:
            self.add_error('no_crn_check', 'Crn is not empty, please uncheck')
            hidden_fields_switcher(self)
        else:
            try:
                if self.cleaned_data.get('crn') is not None:
                    company = CompanyProfile.objects.get(crn=self.cleaned_data['crn'])
                    field = 'crn'
                elif self.cleaned_data.get('tin') is not None:
                    company = CompanyProfile.objects.get(tin=self.cleaned_data['tin'])
                    field = 'tin'
                else:
                    raise CompanyProfile.DoesNotExist

                if not self.request.user.has_perm('aklub.can_edit_all_units'):
                    company.administrative_units.add(self.request.user.administrated_units.first())
                    message = f'Company with this {field} already exist in database and is available now, click here to edit'
                else:
                    message = f'Company with this {field} already exist click here to see'
                url = reverse('admin:aklub_companyprofile_change', args=(company.pk,))
                self.add_error(
                    field,
                    mark_safe(
                        _(f'<a href="{url}">{message}</a>'),
                    ),
                )
                hidden_fields_switcher(self)
            except CompanyProfile.DoesNotExist:
                pass

            if self.cleaned_data['hidden_lock_change'] == 'locked':
                self.data = self.data.copy()
                self.data['hidden_lock_change'] = 'unlocked'
                raise ValidationError('This company is not in database')

            return super().clean()

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


class CompanyProfileChangeForm(CompanyProfileAddForm):
    class Meta(CompanyProfileAddForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super(CompanyProfileAddForm, self).__init__(*args, **kwargs)
        if not self.request.user.has_perm('aklub.can_edit_all_units'):
            self.fields['administrative_units'].queryset = self.instance.administrative_units.all()
            self.fields['administrative_units'].disabled = True

    def clean(self):
        pass
