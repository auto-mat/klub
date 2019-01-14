from django import forms
from django.contrib.auth.models import User
import uuid
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

def username_validation(user, fields):
    if user.username == '':
        user.username = uuid.uuid1()
    else:
        user.username = fields['username']

class UserCreateForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['username'].required = False

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.username = self.cleaned_data['username']

        username_validation(user=user, fields=self.cleaned_data)

        if commit:
            user.save()
        return user

class UserUpdateForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        self.fields['username'].required = False

    def save(self, commit=True):
        user = super(UserChangeForm, self).save(commit=False)
        user.username = self.cleaned_data['username']

        username_validation(user=user, fields=self.cleaned_data)

        if commit:
            user.save()
        return user





