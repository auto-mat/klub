from aklub.models import (
    AdministrativeUnit,
    CompanyProfile,
    DonorPaymentChannel,
    MoneyAccount,
    Payment,
    Profile,
    ProfileEmail,
    Telephone,
    UserProfile,
)

from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from events.models import Event, EventType, Location

from notifications_edit.utils import send_notification_to_is_staff_members

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .exceptions import PasswordsDoNotMatch


class RelatedFieldsMixin(serializers.Serializer):
    money_account = serializers.SlugRelatedField(
        queryset=MoneyAccount.objects.filter(slug__isnull=False), slug_field="slug"
    )
    event = serializers.SlugRelatedField(
        queryset=Event.objects.filter(slug__isnull=False), slug_field="slug"
    )
    telephone = serializers.CharField(
        required=False,
        validators=[
            RegexValidator(
                r"^[0-9+ ]*$",
                _("Telephone must consist of numbers, spaces and plus sign"),
            ),
            MinLengthValidator(9),
        ],
    )
    amount = serializers.IntegerField(required=True)
    regular = serializers.BooleanField(initial=False)


class ValidateEmailMixin:
    def validate_email(self, value):
        return value.lower()


class VSReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorPaymentChannel
        fields = [
            "VS",
        ]


class DonorPaymentChannelNestedSerializer(serializers.ModelSerializer):
    money_account = serializers.SlugRelatedField(
        queryset=MoneyAccount.objects.filter(slug__isnull=False), slug_field="slug"
    )
    event = serializers.SlugRelatedField(
        queryset=Event.objects.filter(slug__isnull=False), slug_field="slug"
    )

    class Meta:
        model = DonorPaymentChannel
        fields = ["money_account", "event", "regular_amount", "regular_frequency", "VS"]
        extra_kwargs = {
            "regular_amount": {"required": True},
            "VS": {"read_only": True},
        }
        depth = 1


class CreateUserProfileSerializer(
    serializers.ModelSerializer, ValidateEmailMixin, RelatedFieldsMixin
):
    """
    Creating legal userprofile with dpch (and also with access to IsAuthenticated views)
    """

    password = serializers.CharField(
        write_only=True, required=False, validators=[validate_password]
    )
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=ProfileEmail.objects.all())]
    )
    userchannels = DonorPaymentChannelNestedSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "password",
            "first_name",
            "last_name",
            "telephone",
            "email",
            "password",
            "userchannels",
        ]
        extra_kwargs = {
            "email": {"required": True},
        }

    def create(self, validated_data):
        dpch_data = validated_data.pop("userchannels")[0]
        telephone = validated_data.pop("telephone", None)

        user = UserProfile.objects.create(
            **validated_data,
        )
        user.administrative_units.add(dpch_data["money_account"].administrative_unit),
        if validated_data.get("password"):
            user.set_password(validated_data.get("password"))
        user.save()

        ProfileEmail.objects.create(
            email=validated_data["email"], user=user, is_primary=True
        )

        if telephone:
            Telephone.objects.create(telephone=telephone, user=user, is_primary=True)

        DonorPaymentChannel.objects.create(
            **dpch_data, user=user, expected_date_of_first_payment=timezone.now()
        )
        return user


get_or_create_user_profile_fields = [
    "first_name",
    "last_name",
    "telephone",
    "email",
    "note",
    "age_group",
    "birth_month",
    "birth_day",
    "street",
    "city",
    "zip_code",
]


class GetOrCreateUserprofile(
    ValidateEmailMixin,
    RelatedFieldsMixin,
    serializers.ModelSerializer,
):
    def get_or_create_user_profile(self):
        vd = self.validated_data
        defaulting_string_fields = [
            "street",
            "city",
            "zip_code",
            "first_name",
            "last_name",
        ]
        nullable_fields = [
            "age_group",
            "birth_month",
            "birth_day",
        ]
        defaults = {
            "sex": vd.get("sex", "unknown"),
        }
        for f in defaulting_string_fields:
            defaults[f] = vd.get(f, "")
        for f in nullable_fields:
            defaults[f] = vd.get(f)
        user, created = UserProfile.objects.get_or_create(
            profileemail__email=vd.get("email"),
            defaults=defaults,
        )
        if not created:
            edited = False
            if user.sex == "unknown":
                user.sex = vd.get("sex", "unknown")
                edited = True
            for f in defaulting_string_fields:
                if getattr(user, f) == "" and vd.get(f):
                    setattr(user, f, vd.get(f))
                    edited = True
            for f in nullable_fields:
                if getattr(user, f) is None and vd.get(f):
                    setattr(user, f, vd.get(f))
                    edited = True
            if edited:
                user.save()

        telephone = vd.get("telephone")
        if telephone:
            Telephone.objects.filter(user=user).update(is_primary=None)
            no, created = Telephone.objects.get_or_create(
                telephone=telephone, user=user
            )
            if not no.is_primary:
                no.is_primary = True
                no.save()

        email = vd.get("email")
        if email:
            ProfileEmail.objects.get_or_create(
                email=email, user=user, defaults={"is_primary": True}
            )

        if vd.get("notes"):
            if user.notes:
                user.notes += "\n\n---\n\n"
            user.notes += vd.get("notes")
            user.save()
        return user, created

    class Meta:
        model = UserProfile
        fields = get_or_create_user_profile_fields


class GetDpchUserProfileSerializer(
    GetOrCreateUserprofile,
):
    """
    Creating legal userprofile with dpch without access to IsAuthentication views
    """

    class Meta:
        model = UserProfile
        fields = [
            "email",
            "first_name",
            "last_name",
            "telephone",
            "street",
            "city",
            "zip_code",
            "money_account",
            "event",
            "birth_day",
            "birth_month",
            "age_group",
            "sex",
            "amount",
            "regular",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
        }

    def get_or_create_user_profile(self):
        user, created = super().get_or_create_user_profile()
        user.administrative_units.add(
            self.validated_data.get("money_account").administrative_unit
        )
        user.save()
        return user, created


class GetDpchCompanyProfileSerializer(
    serializers.ModelSerializer, ValidateEmailMixin, RelatedFieldsMixin
):
    # future version of changed company profile model
    contact_first_name = serializers.CharField(max_length=256, required=False)
    contact_last_name = serializers.CharField(max_length=256, required=False)

    class Meta:
        model = CompanyProfile
        fields = [
            "crn",
            "name",
            "email",
            "telephone",
            "street",
            "city",
            "zip_code",
            "money_account",
            "event",
            "amount",
            "regular",
            "contact_first_name",
            "contact_last_name",
        ]
        extra_kwargs = {
            "name": {"required": True},
            "email": {"required": True},
        }

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as error:
            # catching error to log crn error
            crn_log = error.detail.get("crn")
            if crn_log:
                send_notification_to_is_staff_members(
                    MoneyAccount.objects.get(
                        slug=data["money_account"]
                    ).administrative_unit,
                    _("Wrong CRN (IČO) format"),
                    _(f'User input was: {data["crn"]} and was not created in system'),
                )
            raise error


class EventCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["slug"]


class MoneyAccountCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoneyAccount
        fields = ["slug"]


class DonorPaymetChannelSerializer(serializers.ModelSerializer):
    money_account = serializers.SlugRelatedField(
        queryset=MoneyAccount.objects.filter(slug__isnull=False), slug_field="slug"
    )
    event = serializers.SlugRelatedField(
        queryset=Event.objects.filter(slug__isnull=False), slug_field="slug"
    )
    amount = serializers.IntegerField(required=True)
    date = serializers.DateField(required=True)

    class Meta:
        model = DonorPaymentChannel
        fields = ["event", "money_account", "VS", "amount", "date"]
        extra_kwargs = {
            "event": {"required": True},
        }

    def get_unique_together_validators(self):
        """Overriding method to disable unique together checks"""
        return []


class PaymentSerializer(serializers.ModelSerializer):
    profile_id = serializers.IntegerField(source="user_donor_payment_channel.user.id")

    class Meta:
        model = Payment
        fields = ["amount", "date", "operation_id", "profile_id"]


class InteractionSerizer(serializers.Serializer):
    date = serializers.DateTimeField(required=True)
    event = serializers.SlugRelatedField(
        queryset=Event.objects.filter(slug__isnull=False), slug_field="slug"
    )
    profile_id = serializers.IntegerField(required=True)
    interaction_type = serializers.ChoiceField(choices=("certificate", "confirmation"))
    text = serializers.CharField()


class CreditCardPaymentSerializer(serializers.ModelSerializer, ValidateEmailMixin):
    profile_type = serializers.ChoiceField(
        choices=[("company", "Company profile"), ("user", "User Profile")],
        write_only=True,
    )
    recipient_account = serializers.SlugRelatedField(
        queryset=MoneyAccount.objects.filter(slug__isnull=False), slug_field="slug"
    )
    event = serializers.SlugRelatedField(
        queryset=Event.objects.filter(slug__isnull=False),
        slug_field="slug",
        write_only=True,
    )
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = Payment
        fields = (
            "profile_type",
            "recipient_account",
            "date",
            "amount",
            "event",
            "email",
            "account",
            "bank_code",
            "VS",
            "VS2",
            "SS",
            "KS",
            "BIC",
            "user_identification",
            "done_by",
            "account_name",
            "bank_name",
            "transfer_type",
            "specification",
            "order_id",
        )

    def create(self, validated_data):
        obj = super().create(validated_data)
        obj.type = "creadit_card"
        obj.save()
        return obj


class ProfileSerializer(serializers.ModelSerializer):
    profile_id = serializers.IntegerField(source="id")

    class Meta:
        model = Profile
        fields = ["profile_id"]


class ResetPasswordbyEmailSerializer(serializers.Serializer, ValidateEmailMixin):
    email = serializers.EmailField()


class ResetPasswordbyEmailConfirmSerializer(serializers.Serializer):
    password_1 = serializers.CharField(write_only=True, validators=[validate_password])
    password_2 = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password_1"] == data["password_2"]:
            return data
        else:
            raise PasswordsDoNotMatch()


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = ["name", "slug"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "place", "region", "gps_latitude", "gps_longitude"]


class EventSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    event_type = EventTypeSerializer(read_only=True)
    event_type_id = serializers.PrimaryKeyRelatedField(
        source="event_type", queryset=EventType.objects.all()
    )
    administrative_unit_name = serializers.SerializerMethodField()
    administrative_unit_web_url = serializers.SerializerMethodField()
    diet = serializers.MultipleChoiceField(
        choices=Event.DIET_CHOICES,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "datetime_from",
            "datetime_to",
            "program",
            "intended_for",
            "basic_purpose",
            "opportunity",
            "location",
            "age_from",
            "age_to",
            "start_date",
            "event_type",
            "event_type_id",
            "responsible_person",
            "participation_fee",
            "entry_form_url",
            "web_url",
            "invitation_text_short",
            "working_hours",
            "accommodation",
            "diet",
            "looking_forward_to_you",
            "registration_method",
            "administrative_units",
            "administrative_unit_name",
            "administrative_unit_web_url",
            "invitation_text_1",
            "invitation_text_2",
            "invitation_text_3",
            "invitation_text_4",
            "main_photo",
            "additional_photo_1",
            "additional_photo_2",
            "additional_photo_3",
            "additional_photo_4",
            "additional_photo_5",
            "additional_photo_6",
            "additional_question_1",
            "additional_question_2",
            "additional_question_3",
            "additional_question_4",
            "contact_person_name",
            "contact_person_email",
            "contact_person_telephone",
            "public_on_web_date_from",
            "public_on_web_date_to",
            "public_on_web",
        ]

    def get_administrative_unit_name(self, obj):
        try:
            # there is always one
            name = obj.administrative_units.all()[0].name
        except IndexError:
            name = ""
        return name

    def get_administrative_unit_web_url(self, obj):
        try:
            # there is always one
            web_url = obj.administrative_units.all()[0].web_url
        except IndexError:
            web_url = ""
        return web_url


class AdministrativeUnitSerializer(serializers.ModelSerializer):
    president_name = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = AdministrativeUnit
        fields = [
            "id",
            "name",
            "street",
            "city",
            "zip_code",
            "telephone",
            "from_email_address",
            "web_url",
            "president_name",
            "manager_name",
            "gps_latitude",
            "gps_longitude",
            "level",
        ]

    def get_president_name(self, obj):
        return obj.president.get_full_name() if obj.president else None

    def get_manager_name(self, obj):
        return obj.manager.get_full_name() if obj.manager else None
