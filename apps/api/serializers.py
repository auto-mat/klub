from aklub.models import CompanyProfile, Event, MoneyAccount, UserProfile

from django.core.validators import MinLengthValidator, RegexValidator
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class RelatedFieldsMixin(serializers.Serializer):
    money_account = serializers.SlugRelatedField(queryset=MoneyAccount.objects.filter(slug__isnull=False), slug_field='slug')
    event = serializers.SlugRelatedField(queryset=Event.objects.filter(slug__isnull=False), slug_field='slug')
    telephone = serializers.CharField(
        required=True,
        validators=[RegexValidator(r'^[0-9+ ]*$', _('Telephone must consist of numbers, spaces and plus sign')), MinLengthValidator(9)],
    )


class GetDpchUserProfileSerializer(serializers.ModelSerializer, RelatedFieldsMixin):
    class Meta:
        model = UserProfile
        fields = [
            'email', 'first_name', 'last_name', 'telephone', 'street',
            'city', 'zip_code', 'money_account', 'event', 'birth_day', 'birth_month',
            'age_group', 'birth_month', 'birth_day',
            ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }


class GetDpchCompanyProfileSerializer(serializers.ModelSerializer, RelatedFieldsMixin):
    class Meta:
        model = CompanyProfile
        fields = ['crn', 'name', 'email', 'telephone', 'street', 'city', 'zip_code', 'money_account', 'event']
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
        }
