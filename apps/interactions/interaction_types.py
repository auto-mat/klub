from .models import InteractionType, InteractionCategory


def volunteer_interaction_category():
    cat, _ = InteractionCategory.objects.get_or_create(
        slug="volunteer",
        display=True,
        defaults={"category": "Nabídka o pomoci"},
    )
    return cat


def event_interaction_category():
    cat, _ = InteractionCategory.objects.get_or_create(
        slug="event_interaction",
        display=True,
        defaults={"category": "Účast na akci"},
    )
    return cat


def event_registration_interaction_type():
    itype, _ = InteractionType.objects.get_or_create(
        slug="event_registration",
        category=event_interaction_category(),
        defaults={"name": "Registrace do akci"},
    )
    return itype


def event_attendance_interaction_type():
    itype, _ = InteractionType.objects.get_or_create(
        slug="event_attendance",
        category=event_interaction_category(),
        defaults={"name": "Účast na akci"},
    )
    return itype


def membership_interaction_category():
    cat, _ = InteractionCategory.objects.get_or_create(
        slug="membership",
        display=True,
        defaults={"category": "Členství"},
    )
    return cat


def membership_application_interaction_type():
    itype, _ = InteractionType.objects.get_or_create(
        slug="membership-application",
        category=membership_interaction_category(),
        defaults={"name": "Žadost o Členství"},
    )
    return itype


def membership_approval_interaction_type():
    itype, _ = InteractionType.objects.get_or_create(
        slug="membership-approval",
        category=membership_interaction_category(),
        defaults={"name": "Přijetí Členství"},
    )
    return itype
