from .modules import InteractionType, InteractionCategory


def offer_help_interaction_category():
    cat, _ = InteractionCategory.objects.get_or_create(
        slug="offer_help",
        display=True,
        defaults={"category": "Nabídka o pomoci"},
    )
    return cat

def event_attendance_interaction_category():
    cat, _ = InteractionCategory.objects.get_or_create(
        slug="event_attendance",
        display=True,
        defaults = {"category": "Účast na akci"},
    )
    return cat

def event_registration_interaction_type():
    type, _ = InteractionType.objects.get_or_create(
        slug="event_registration",
        category=event_attendance_interaction_category(),
        defaults = {"name": "Registrace do akci"},
    )
    return type


def event_attendance_interaction_type():
    type, _ = InteractionType.objects.get_or_create(
        slug="event_attendance",
        category=event_attendance_interaction_category(),
        defaults = {"name": "Účast na akci"}
    )
    return type

def membership_interaction_category():
    cat, _ = InteractionCategory.objects.get_or_create(
        slug="membership",
        display=True,
        defaults = {"category": "Členství"},
    )
    return cat


def get_interaction_category(slug):
    categories = {
        "membership": membership_interaction_category,
        "offer_help": offer_help_interaction_category,
        "event_attendance": event_attendance_interaction_category,
    }
    if slug in categories:
        return categories[slug]()
    else:
        raise InteractionCategory.DoesNotExist()
