from aklub.models import (
    AdministrativeUnit, CompanyProfile, DonorPaymentChannel, MoneyAccount, Payment, Profile, ProfileEmail, Telephone, UserProfile,
)

from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from events.models import Event, Location, OrganizationTeam

from notifications_edit.utils import send_notification_to_is_staff_members

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .exceptions import PasswordsDoNotMatch


class RelatedFieldsMixin(serializers.Serializer):
    money_account = serializers.SlugRelatedField(queryset=MoneyAccount.objects.filter(slug__isnull=False), slug_field='slug')
    event = serializers.SlugRelatedField(queryset=Event.objects.filter(slug__isnull=False), slug_field='slug')
    telephone = serializers.CharField(
        required=False,
        validators=[RegexValidator(r'^[0-9+ ]*$', _('Telephone must consist of numbers, spaces and plus sign')), MinLengthValidator(9)],
    )
    amount = serializers.IntegerField(required=True)
    regular = serializers.BooleanField(initial=False)


class ValidateEmailMixin:
    def validate_email(self, value):
        return value.lower()


class VSReturnSerializer(serializers.ModelSerializer):

    class Meta:
        model = DonorPaymentChannel
        fields = ['VS', ]


class GetDpchUserProfileSerializer(serializers.ModelSerializer, ValidateEmailMixin, RelatedFieldsMixin):
    """
    Creating legal userprofile with dpch without access to IsAuthentication views
    """
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


class GetDpchCompanyProfileSerializer(serializers.ModelSerializer, ValidateEmailMixin, RelatedFieldsMixin):
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

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as error:
            # catching error to log crn error
            crn_log = error.detail.get('crn')
            if crn_log:
                send_notification_to_is_staff_members(
                    MoneyAccount.objects.get(slug=data['money_account']).administrative_unit,
                    _('Wrong format of crn'),
                    _(f'User input was: {data["crn"]} and was not create in system'),
                )
            raise error


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


class CreditCardPaymentSerializer(serializers.ModelSerializer, ValidateEmailMixin):
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


class CreateUserProfileInteractionSerializer(serializers.ModelSerializer, ValidateEmailMixin, RelatedFieldsMixin):
    additional_question_1 = serializers.CharField(required=False)
    additional_question_2 = serializers.CharField(required=False)
    additional_question_3 = serializers.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = (
            'first_name', 'last_name', 'telephone', 'email', 'note', 'age_group', 'birth_month', 'birth_day', 'event',
            'additional_question_1', 'additional_question_2', 'additional_question_3',
        )
        extra_kwargs = {
            'email': {'required': True},
        }


class CreateUserProfileSerializer(serializers.ModelSerializer, ValidateEmailMixin, RelatedFieldsMixin):
    """
    Creating legal userprofile with dpch (and also with access to IsAuthenticated views)
    """
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


class ResetPasswordbyEmailSerializer(serializers.Serializer, ValidateEmailMixin):
    email = serializers.EmailField()


class ResetPasswordbyEmailConfirmSerializer(serializers.Serializer):
    password_1 = serializers.CharField(write_only=True, validators=[validate_password])
    password_2 = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password_1'] == data['password_2']:
            return data
        else:
            raise PasswordsDoNotMatch()


class OrganizationTeamSerializer(serializers.ModelSerializer):
    first_name = serializers.ReadOnlyField(source='profile.first_name')
    last_name = serializers.ReadOnlyField(source='profile.last_name')
    telephone = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationTeam
        fields = ["id", "first_name", "last_name", "telephone", "email"]

    def get_email(self, obj):
        # TODO: waiting for polymorphic select related fix:
        # for email in obj.profile.userprofile.profileemail_set.all()
        #    if email.is_primary:
        #        return email.email
        userprofile = obj.profile.get_real_instance()
        try:
            email = userprofile.profileemail_set.get(is_primary=True).email
        except ProfileEmail.DoesNotExist:
            email = None
        return email

    def get_telephone(self, obj):
        # TODO: waiting for polymorphic select related fix:
        # for telephone in obj.profile.userprofile.telephone_set.all()
        #    if telephone.is_primary:
        #        return telephone.telephone
        userprofile = obj.profile.get_real_instance()
        try:
            telephone = userprofile.telephone_set.get(is_primary=True).telephone
        except Telephone.DoesNotExist:
            telephone = None
        return telephone


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["name", "place", "region", "gps"]


class EventSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    organization_team = OrganizationTeamSerializer(read_only=True, many=True, source="filtered_organization_team")
    indended_for = serializers.CharField(source='get_indended_for_display')
    program = serializers.CharField(source='get_program_display')

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'slug', 'date_from', 'date_to', 'program', 'indended_for',
            'location', 'age_from', 'age_to', 'start_date',
            'participation_fee', 'organization_team', 'entry_form_url', 'web_url', 'invitation_text_short',
            'invitation_text_1', 'invitation_text_2', 'invitation_text_3',
            'invitation_text_4', 'main_photo', 'additional_photo_1', 'additional_photo_2',
            'additional_photo_3', 'additional_photo_4', 'additional_photo_5', 'additional_photo_6',
        ]


class AdministrativeUnitSerializer(serializers.ModelSerializer):
    president_name = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    level = serializers.CharField(source='get_level_display')

    class Meta:
        model = AdministrativeUnit
        fields = [
            'id', 'name', 'city', 'zip_code', 'telephone', 'from_email_address', 'web_url', 'president_name', 'manager_name',
            'gps_latitude', 'gps_longitude', 'level',
        ]

    def get_president_name(self, obj):
        return obj.president.get_full_name() if obj.president else None

    def get_manager_name(self, obj):
        return obj.manager.get_full_name() if obj.manager else None
