from django.urls import reverse_lazy
from django.contrib.auth.forms import UserChangeForm, UserCreationForm, \
    ReadOnlyPasswordHashField

from .views import get_unique_username


def username_validation(user, fields):
    if user.username == '':
        user.username = get_unique_username(fields['email'])
    else:
        user.username = fields['username']


class UserCreateForm(UserCreationForm):
    password = ReadOnlyPasswordHashField()

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['username'].required = False
        self.fields['password'].help_text = 'You can set password in the next step or anytime in user detail form'

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.username = self.cleaned_data['username']
        username_validation(user=user, fields=self.cleaned_data)

        if commit:
            user.save()
        return user


class UserUpdateForm(UserChangeForm):
    password = ReadOnlyPasswordHashField()

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['password'].help_text = ("Raw passwords are not stored, so there is no way to see "
                                             "this user's password, but you can <a href=\"%s\"> "
                                             "<strong>Change the Password</strong> using this form</a>."
                                             ) % reverse_lazy('admin:auth_user_password_change',
                                                              args=[self.instance.id])

    def save(self, commit=True):
        user = super(UserChangeForm, self).save(commit=False)
        user.username = self.cleaned_data['username']
        username_validation(user=user, fields=self.cleaned_data)

        if commit:
            user.save()
        return user
