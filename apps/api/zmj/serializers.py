from rest_framework import serializers

from aklub.models import (
    CompanyProfile,
    CompanyType,
    Preference,
    ProfileEmail,
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
    sex = serializers.ChoiceField(
        required=False, allow_blank=True, choices=UserProfile.GENDER
    )
    send_mailing_lists = serializers.BooleanField(required=False)
    newsletter_on = serializers.BooleanField(required=False, allow_null=True)

    # Event fields
    event_name = serializers.CharField(required=True)
    event_date = serializers.DateTimeField(required=True)
    gps_latitude = serializers.FloatField(required=False, allow_null=True)
    gps_longitude = serializers.FloatField(required=False, allow_null=True)
    place = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    space_type = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    space_area = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    space_rent = serializers.BooleanField(required=False, default=False)
    activities = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # Company fields (optional)
    company_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    company_type_id = serializers.PrimaryKeyRelatedField(
        queryset=CompanyType.objects.all(), required=False, allow_null=True
    )
    company_crn = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    company_tin = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    # Organizers list (optional) - these are NOT users, just contact info
    organizers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(allow_blank=True, allow_null=True)
        ),
        required=False,
        allow_empty=True,
    )

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
        activities = validated_data.pop("activities", None)
        company_name = validated_data.pop("company_name", None)
        company_type_id = validated_data.pop("company_type_id", None)
        company_crn = validated_data.pop("company_crn", None)
        company_tin = validated_data.pop("company_tin", None)
        organizers = validated_data.pop("organizers", [])

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

        # Add organizer link for the user
        organizer_position, _ = OrganizationPosition.objects.get_or_create(
            name="Event creator"
        )
        OrganizationTeam.objects.get_or_create(
            profile=user,
            event=event,
            position=organizer_position,
        )

        # Create company if company info is provided
        company = None
        if company_name or company_crn:
            company = CompanyProfile.objects.create(
                name=company_name,
                crn=company_crn,
                type=company_type_id,
                tin=company_tin,
            )

            # Link company to user's administrative units
            if user.administrative_units.exists():
                company.administrative_units.set(user.administrative_units.all())

            # Link company to event via OrganizationTeam
            OrganizationTeam.objects.get_or_create(
                profile=company,
                event=event,
                position=organizer_position,
            )

        # Create organizers (as UserProfile entries without authentication)
        if organizers:
            organizer_position_obj, _ = OrganizationPosition.objects.get_or_create(
                name="Organizer"
            )
            for organizer_data in organizers:
                first_name = organizer_data.get("first_name", "").strip()
                last_name = organizer_data.get("last_name", "").strip()
                email = organizer_data.get("email", "").strip()
                telephone = organizer_data.get("telephone", "").strip()

                # Skip if no name or contact info
                if not (first_name or last_name) or not (email or telephone):
                    continue

                # Create new organizer profile
                organizer_profile = UserProfile.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                )

                # Add email if provided
                if email:
                    ProfileEmail.objects.create(
                        email=email, user=organizer_profile, is_primary=True
                    )

                # Add telephone if provided
                if telephone:
                    Telephone.objects.create(
                        telephone=telephone, user=organizer_profile, is_primary=True
                    )

                # Link to user's administrative units
                if user.administrative_units.exists():
                    organizer_profile.administrative_units.set(
                        user.administrative_units.all()
                    )

                # Create OrganizationTeam entry
                OrganizationTeam.objects.create(
                    profile=organizer_profile,
                    event=event,
                    position=organizer_position_obj,
                )

        return user


class UpdateEventSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    date = serializers.DateTimeField(required=False, allow_null=True)
    place = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    def update(self, instance, validated_data):
        """Update event and location"""
        event = instance
        date = validated_data.pop("date", None)
        place = validated_data.pop("place", None)
        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)

        # Update event name
        if "name" in validated_data:
            event.name = validated_data["name"]
            event.save()

        # Update event date
        if date is not None:
            event.start_date = date
            event.datetime_from = date
            event.save()

        # Update location
        if place is not None or latitude is not None or longitude is not None:
            if event.location:
                location = event.location
            else:
                # Create new location if it doesn't exist
                location = Location.objects.create(
                    name=place or event.name or "Location",
                    place=place or "",
                )
                event.location = location
                event.save()

            # Update location fields
            if place is not None:
                location.place = place
                if not location.name:
                    location.name = place or event.name or "Location"
            if latitude is not None:
                location.gps_latitude = latitude
            if longitude is not None:
                location.gps_longitude = longitude
            location.save()

        return event


class CompanySerializer(serializers.Serializer):
    """Serializer for company fields: name, company_type, crn, tin"""

    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_type = serializers.PrimaryKeyRelatedField(
        queryset=CompanyType.objects.all(),
        required=False,
        allow_null=True,
        source="type",
    )
    crn = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    tin = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def to_representation(self, instance):
        """Custom representation to return company data"""
        data = {
            "name": instance.name,
            "company_type": instance.type.id if instance.type else None,
            "company_type_name": instance.type.type if instance.type else None,
            "crn": instance.crn,
            "tin": instance.tin,
        }
        return data

    def update(self, instance, validated_data):
        """Update company fields"""
        company = instance

        # Update name if provided
        if "name" in validated_data:
            company.name = validated_data["name"]

        # Update type (company_type) if provided
        if "type" in validated_data:
            company.type = validated_data["type"]

        # Update crn if provided
        if "crn" in validated_data:
            company.crn = validated_data["crn"]

        # Update tin if provided
        if "tin" in validated_data:
            company.tin = validated_data["tin"]

        company.save()
        return company


class EventContentSerializer(serializers.Serializer):
    """
    Serializer for event content fields:
    - main_photo (file upload)
    - description
    - url, url_title
    - url1, url_title1
    - url2, url_title2
    """

    main_photo = serializers.FileField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    url_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    url1 = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    url_title1 = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    url2 = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    url_title2 = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def to_representation(self, instance):
        """Return event content data, converting main_photo to URL"""
        main_photo_url = None
        if instance.main_photo:
            try:
                main_photo_url = instance.main_photo.url
            except (ValueError, AttributeError):
                main_photo_url = None

        data = {
            "main_photo": main_photo_url,
            "description": instance.description,
            "url": instance.url,
            "url_title": instance.url_title,
            "url1": instance.url1,
            "url_title1": instance.url_title1,
            "url2": instance.url2,
            "url_title2": instance.url_title2,
        }
        return data

    def update(self, instance, validated_data):
        """Update event content fields"""
        event = instance

        # Update main_photo if provided
        if "main_photo" in validated_data:
            event.main_photo = validated_data["main_photo"]

        # Update description if provided
        if "description" in validated_data:
            event.description = validated_data["description"]

        # Update url and url_title if provided
        if "url" in validated_data:
            event.url = validated_data["url"]
        if "url_title" in validated_data:
            event.url_title = validated_data["url_title"]

        # Update url1 and url_title1 if provided
        if "url1" in validated_data:
            event.url1 = validated_data["url1"]
        if "url_title1" in validated_data:
            event.url_title1 = validated_data["url_title1"]

        # Update url2 and url_title2 if provided
        if "url2" in validated_data:
            event.url2 = validated_data["url2"]
        if "url_title2" in validated_data:
            event.url_title2 = validated_data["url_title2"]

        event.save()
        return event


class OrganizerSerializer(serializers.Serializer):
    """
    Organizer contact info for an event.

    - `id` is optional on input (if missing => create new organizer profile)
    - email/telephone are stored in `ProfileEmail`/`Telephone` (primary values)
    """

    id = serializers.IntegerField(required=False, allow_null=True)
    first_name = serializers.CharField(required=True, allow_blank=True, allow_null=True)
    last_name = serializers.CharField(required=True, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    telephone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
