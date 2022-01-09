from rest_framework import routers
from . import events_unit
from . import locations_unit
from . import event_type_unit

router = routers.DefaultRouter()
router.register(r"events", events_unit.EventSet, basename="frontend_events")
router.register(r"event-type", event_type_unit.EventTypeSet, basename="frontend_event-type")
router.register(r"locations", locations_unit.LocationSet, basename="frontend_locations")
