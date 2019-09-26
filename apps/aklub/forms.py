# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UserChangeForm, UserCreationForm, UsernameField
from django.shortcuts import reverse
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import AdministrativeUnit, CompanyProfile, ProfileEmail
from .views import get_unique_username

Profile = get_user_model()


def username_validation(user, fields):
    if user.username == '':
        user.username = get_unique_username(fields['email'])
    else:
        user.username = fields['username']


class UserCreateForm(UserCreationForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Profile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['username'].required = False
        self.fields['password'].help_text = 'You can set password in the next step or anytime in user detail form'

    def clean(self):
        if self.cleaned_data['email'] is None:
            return super().clean()

        email, created = ProfileEmail.objects.get_or_create(email=self.cleaned_data['email'])
        if created is True:
            return super().clean()

        else:
            url = reverse('admin:aklub_userprofile_change', args=(email.user.pk,))
            self.add_error(
                'email',
                mark_safe(
                    _(f'<a href="{url}">User with this email already exist in database, click here to edit</a>'),
                ),
            )

    def save(self, commit=True):
        user = super().save(commit=False)

        user.username = self.cleaned_data['username']
        username_validation(user=user, fields=self.cleaned_data)
        email = user.email
        user.email = None
        user.save()
        if self.cleaned_data['email'] is not None:
            ProfileEmail.objects.create(email=email, user=user, is_primary=True)
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

    def clean(self):
        if self.cleaned_data['email'] is None:
            return super().clean()

        email, created = ProfileEmail.objects.get_or_create(email=self.cleaned_data['email'])
        if created is True:
            return super().clean()

        else:
            user = email.user
            administrated_unit = AdministrativeUnit.objects.get(id=self.request.user.administrated_units.first().id)
            user.administrative_units.add(administrated_unit)
            url = reverse('admin:aklub_userprofile_change', args=(user.pk,))
            self.add_error(
                'email',
                mark_safe(
                    _(f'<a href="{url}">User with this email already exist in database and is available now, click here to edit</a>'),
                ),
            )

    def save(self, commit=True):
        user = super().save(commit=False)
        email = user.email
        user.email = None
        user.save()
        ProfileEmail.objects.create(email=email, user=user, is_primary=True)
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['administrative_units'].queryset = self.request.user.administrated_units.all()
        self.fields['administrative_units'].required = True


class UnitUserProfileChangeForm(UnitUserProfileAddForm):

    class Meta(UnitUserProfileAddForm.Meta):
        pass

    def clean(self):
        pass

    def __init__(self, *args, **kwargs):
        super(UnitUserProfileAddForm, self).__init__(*args, **kwargs)
        self.fields['administrative_units'].queryset = self.instance.administrative_units.all()
        self.fields['administrative_units'].disabled = True


class CompanyProfileAddForm(forms.ModelForm):
    no_crn_check = forms.BooleanField(
                required=False,
                initial=False,
    )

    class Meta:
        model = Profile
        fields = '__all__'

    def clean(self):
        if self.cleaned_data.get('crn') is None and self.cleaned_data.get('no_crn_check') is False:
            self.add_error('no_crn_check', 'Please confirm empty crn number')
        elif self.cleaned_data.get('crn') is not None and self.cleaned_data.get('no_crn_check') is True:
            self.add_error('no_crn_check', 'Crn is not empty, please uncheck')
        else:
            try:
                if self.cleaned_data.get('crn') is not None:
                    company = CompanyProfile.objects.get(crn=self.cleaned_data['crn'])
                    field = 'crn'
                elif self.cleaned_data.get('tin') is not None:
                    company = CompanyProfile.objects.get(tin=self.cleaned_data['tin'])
                    field = 'tin'
                else:
                    return super().clean()

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
            except CompanyProfile.DoesNotExist:
                pass
        return super().clean()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.request.user.has_perm('aklub.can_edit_all_units'):
            self.fields['administrative_units'].queryset = self.request.user.administrated_units.all()
            self.fields['administrative_units'].required = True


class CompanyProfileChangeForm(CompanyProfileAddForm):
    class Meta(CompanyProfileAddForm.Meta):
        pass

    def clean(self):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.request.user.has_perm('aklub.can_edit_all_units'):
            self.fields['administrative_units'].queryset = self.instance.administrative_units.all()
            self.fields['administrative_units'].disabled = True
