from aklub.models import CompanyProfile, DonorPaymentChannel, Event, MoneyAccount, Payment, ProfileEmail, UserProfile

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
    amount = serializers.IntegerField(required=True)
    regular = serializers.BooleanField(initial=False)


class VSReturnSerializer(serializers.ModelSerializer):

    class Meta:
        model = DonorPaymentChannel
        fields = ['VS', ]


class GetDpchUserProfileSerializer(serializers.ModelSerializer, RelatedFieldsMixin):

    class Meta:
        model = UserProfile
        fields = [
            'email', 'first_name', 'last_name', 'telephone', 'street',
            'city', 'zip_code', 'money_account', 'event', 'birth_day', 'birth_month',
            'age_group', 'sex', 'amount', 'regular',
            ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }


class GetDpchCompanyProfileSerializer(serializers.ModelSerializer, RelatedFieldsMixin):
    # future version of changed company profile model
    contact_first_name = serializers.CharField(max_length=256, required=False)
    contact_last_name = serializers.CharField(max_length=256, required=False)

    class Meta:
        model = CompanyProfile
        fields = [
            'crn', 'name', 'email', 'telephone', 'street', 'city',
            'zip_code', 'money_account', 'event', 'amount', 'regular',
            'contact_first_name', 'contact_last_name',
            ]
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
        }


class EventCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['slug']


class MoneyAccountCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoneyAccount
        fields = ['slug']


class DonorPaymetChannelSerializer(serializers.ModelSerializer):
    money_account = serializers.SlugRelatedField(queryset=MoneyAccount.objects.filter(slug__isnull=False), slug_field='slug')
    event = serializers.SlugRelatedField(queryset=Event.objects.filter(slug__isnull=False), slug_field='slug')
    amount = serializers.IntegerField(required=True)
    date = serializers.DateField(required=True)

    class Meta:
        model = DonorPaymentChannel
        fields = ['event', 'money_account', 'VS', 'amount', 'date']
        extra_kwargs = {
            'event': {'required': True},
        }

    def get_unique_together_validators(self):
        """Overriding method to disable unique together checks"""
        return []


class PaymentSerializer(serializers.ModelSerializer):
    profile_id = serializers.IntegerField(source='user_donor_payment_channel.user.id')

    class Meta:
        model = Payment
        fields = ['amount', 'date', 'profile_id']


class InteractionSerizer(serializers.Serializer):
    date = serializers.DateTimeField(required=True)
    event = serializers.SlugRelatedField(queryset=Event.objects.filter(slug__isnull=False), slug_field='slug')
    profile_id = serializers.IntegerField(required=True)
    interaction_type = serializers.ChoiceField(choices=("certificate", "confirmation"))
    text = serializers.CharField()


class CreditCardPaymentSerializer(serializers.ModelSerializer):
    profile_type = serializers.ChoiceField(choices=[('company', 'Company profile'), ('user', 'User Profile')], write_only=True)
    recipient_account = serializers.SlugRelatedField(queryset=MoneyAccount.objects.filter(slug__isnull=False), slug_field='slug')
    event = serializers.SlugRelatedField(queryset=Event.objects.filter(slug__isnull=False), slug_field='slug', write_only=True)
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = Payment
        fields = (
            'profile_type', 'recipient_account', 'date', 'amount', 'event', 'email', 'account', 'bank_code', 'VS', 'VS2',
            'SS', 'KS', 'BIC', 'user_identification', 'done_by', 'account_name', 'bank_name', 'transfer_type',
            'specification', 'order_id',
        )

    def create(self, validated_data):
        obj = super().create(validated_data)
        obj.type = 'creadit_card'
        obj.save()
        return obj
