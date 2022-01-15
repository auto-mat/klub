from rest_framework import routers
from . import events_unit
from . import locations_unit
from . import users_unit
from . import event_type_unit
from . import my_events_unit
from . import organized_events_unit

router = routers.DefaultRouter()
router.register(r"events", events_unit.EventSet, basename="frontend_events")
router.register(r"my_events", my_events_unit.MyEventsSet, basename="frontend_my_events")
router.register(
    r"organized_events",
    organized_events_unit.OrganizedEventsSet,
    basename="frontend_organized_events",
)
router.register(
    r"event-type", event_type_unit.EventTypeSet, basename="frontend_event-type"
)
router.register(r"locations", locations_unit.LocationSet, basename="frontend_locations")
router.register(r"users", users_unit.UserSet, basename="frontend_users")
