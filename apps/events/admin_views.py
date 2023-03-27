from django.contrib.admin.views.main import ChangeList


class EventChangeList(ChangeList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.list_display.insert(
            self.list_display.index("note") + 1,
            "event",
        )
        self.list_editable = list(self.list_editable)
        self.list_editable.append("event")
