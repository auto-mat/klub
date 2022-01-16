from interactions.models import Interaction, InteractionType

from rest_framework import serializers


class EventTypeDoesNotExist(serializers.ValidationError):
    status_code = 405
    default_detail = {"type__slug": "Interaction type does not exist"}


class EventInteractionSerializer(serializers.ModelSerializer):
    type__slug = serializers.CharField(source="type.slug")

    def validate(self, data):
        validated_data = super().validate(data)

        try:
            validated_data["type"] = InteractionType.objects.get(
                slug=data["type"]["slug"]
            )
        except InteractionType.DoesNotExist:
            raise EventTypeDoesNotExist

        validated_data["administrative_unit"] = validated_data[
            "event"
        ].event_type.administrative_unit
        validated_data["date_from"] = validated_data["event"].start_date
        if validated_data["date_from"] is None:
            validated_data["date_from"] = datetime.date.today()
        return validated_data

    class Meta:
        model = Interaction
        fields = (
            "id",
            "event",
            "summary" "updated",
            "created",
            "type__slug",
            "user",
        )


class UserOwnedEventInteractionSerializer(EventInteractionSerializer):
    class Meta:
        model = Interaction
        fields = (
            "id",
            "event",
            "note",
            "updated",
            "created",
            "type__slug",
            "note",
        )

    def validate(self, data):
        validated_data = super().validate(data)
        validated_data["user"] = self.context["request"].user
        return validated_data
