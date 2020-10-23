from aklub.models import CompanyProfile, DonorPaymentChannel, Event, MoneyAccount, Payment, Profile, ProfileEmail, Telephone, UserProfile

from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class RelatedFieldsMixin(serializers.Serializer):
    money_account = serializers.SlugRelatedField(queryset=MoneyAccount.objects.filter(slug__isnull=False), slug_field='slug')
    event = serializers.SlugRelatedField(queryset=Event.objects.filter(slug__isnull=False), slug_field='slug')
    telephone = serializers.CharField(
        required=False,
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
        fields = ['amount', 'date', 'operation_id', 'profile_id']


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


class ProfileSerializer(serializers.ModelSerializer):
    profile_id = serializers.IntegerField(source='id')

    class Meta:
        model = Profile
        fields = ['profile_id']


class DonorPaymentChannelNestedSerializer(serializers.ModelSerializer):
    money_account = serializers.SlugRelatedField(queryset=MoneyAccount.objects.filter(slug__isnull=False), slug_field='slug')
    event = serializers.SlugRelatedField(queryset=Event.objects.filter(slug__isnull=False), slug_field='slug')

    class Meta:
        model = DonorPaymentChannel
        fields = ['money_account', 'event', 'regular_amount', 'regular_frequency', 'VS']
        extra_kwargs = {
            'regular_amount': {'required': True},
            'VS': {'read_only': True},
        }
        depth = 1


class CreateUserProfileSerializer(serializers.ModelSerializer, RelatedFieldsMixin):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    email = serializers.EmailField(validators=[UniqueValidator(queryset=ProfileEmail.objects.all())])
    userchannels = DonorPaymentChannelNestedSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = [
            'username', 'password', 'first_name', 'last_name', 'telephone',
            'email', 'password', 'userchannels',
        ]
        extra_kwargs = {
            'email': {'required': True},
        }

    def create(self, validated_data):
        dpch_data = validated_data.pop('userchannels')[0]
        telephone = validated_data.pop('telephone', None)

        user = UserProfile.objects.create(
            **validated_data,
            )
        user.administrative_units.add(dpch_data['money_account'].administrative_unit),
        if validated_data.get('password'):
            user.set_password(validated_data.get('password'))
        user.save()

        ProfileEmail.objects.create(email=validated_data['email'], user=user, is_primary=True)

        if telephone:
            Telephone.objects.create(telephone=telephone, user=user, is_primary=True)

        DonorPaymentChannel.objects.create(**dpch_data, user=user, expected_date_of_first_payment=timezone.now())
        return user
