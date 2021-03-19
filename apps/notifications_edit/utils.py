from aklub.models import Profile

from notifications.signals import notify


def send_notification_to_is_staff_members(administrative_unit, verb, description):
    """
    sending notification to every user of admin team uder administrative_unit
    """
    profiles = Profile.objects.filter(is_staff=True, administrated_units=administrative_unit)
    notify.send(
        sender=administrative_unit,
        recipient=profiles,
        verb=verb,
        description=description,
    )
