from rest_framework import serializers

from aklub.models import (
    Preference,
    Telephone,
    UserProfile,
)
from events.models import (
    Event,
    Location,
    OrganizationPosition,
    OrganizationTeam,
)


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    telephone = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    class Meta:
        model = UserProfile
        fields = ["first_name", "last_name", "telephone", "sex", "language"]
        extra_kwargs = {
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
            "sex": {"required": False, "allow_blank": True},
            "language": {"required": False, "allow_blank": True},
        }

    def update(self, instance, validated_data):
        telephone = validated_data.pop("telephone", None)
        instance = super().update(instance, validated_data)

        # Telephone update
        if telephone is not None:
            if telephone:
                Telephone.objects.filter(user=instance).update(is_primary=None)
                tel, created = Telephone.objects.get_or_create(
                    telephone=telephone, user=instance
                )
                if not tel.is_primary:
                    tel.is_primary = True
                    tel.save()
            else:
                Telephone.objects.filter(user=instance, is_primary=True).update(
                    is_primary=None
                )

        return instance


class RegistrationSerializer(serializers.Serializer):
    # Profile fields
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    telephone = serializers.CharField(required=True)
    sex = serializers.CharField(required=False, allow_blank=True)
    send_mailing_lists = serializers.BooleanField(required=False)
    newsletter_on = serializers.BooleanField(required=False, allow_null=True)

    # Event fields
    event_name = serializers.CharField(required=True)
    event_date = serializers.DateTimeField(required=True)
    gps_latitude = serializers.FloatField(required=False, allow_null=True)
    gps_longitude = serializers.FloatField(required=False, allow_null=True)
    place = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    space_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    space_area = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    space_rent = serializers.BooleanField(required=False, default=False)
    activities = serializers.CharField(required=False, allow_blank=True, default="")

    def update(self, instance, validated_data):
        # Update user profile fields
        user = instance
        telephone = validated_data.pop("telephone", None)
        send_mailing_lists = validated_data.pop("send_mailing_lists", None)
        newsletter_on = validated_data.pop("newsletter_on", None)
        event_name = validated_data.pop("event_name")
        event_date = validated_data.pop("event_date")
        gps_latitude = validated_data.pop("gps_latitude", None)
        gps_longitude = validated_data.pop("gps_longitude", None)
        place = validated_data.pop("place", None)
        space_type = validated_data.pop("space_type", None)
        space_area = validated_data.pop("space_area", None)
        space_rent = validated_data.pop("space_rent", False)
        activities = validated_data.pop("activities", "")

        # Update basic profile fields
        for field in ["first_name", "last_name", "sex"]:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        user.save()

        # Update telephone
        if telephone is not None:
            if telephone:
                Telephone.objects.filter(user=user).update(is_primary=None)
                tel, created = Telephone.objects.get_or_create(
                    telephone=telephone, user=user
                )
                if not tel.is_primary:
                    tel.is_primary = True
                    tel.save()
            else:
                Telephone.objects.filter(user=user, is_primary=True).update(
                    is_primary=None
                )

        # Update preferences
        if send_mailing_lists is not None or newsletter_on is not None:
            for admin_unit in user.administrative_units.all():
                preference, created = Preference.objects.get_or_create(
                    user=user,
                    administrative_unit=admin_unit,
                )
                if send_mailing_lists is not None:
                    preference.send_mailing_lists = send_mailing_lists
                if newsletter_on is not None:
                    preference.newsletter_on = newsletter_on
                preference.save()

        # Create location for the event
        location = Location.objects.create(
            name=place or event_name,
            place=place or "",
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
        )

        # Create the event the user organizes
        event = Event.objects.create(
            name=event_name,
            start_date=event_date,
            datetime_from=event_date,
            location=location,
            space_type=space_type,
            space_area=space_area,
            space_rent=space_rent,
            activities=activities,
        )

        # Attach user's administrative units if any
        if user.administrative_units.exists():
            event.administrative_units.set(user.administrative_units.all())

        # Add organizer link
        organizer_position, _ = OrganizationPosition.objects.get_or_create(
            name="Event creator"
        )
        OrganizationTeam.objects.get_or_create(
            profile=user,
            event=event,
            position=organizer_position,
        )

        return user
