from ..utils import send_notification_to_is_staff_members


class TestCreateNotification:
    def test_send_notification_to_is_staff_members(
        self,
        userprofile_superuser_1,
    ):
        send_notification_to_is_staff_members(
            userprofile_superuser_1.administrated_units.first(),
            "test_verb",
            "test_description",
        )
        notifications = userprofile_superuser_1.notifications.all()
        assert notifications.count() == 1
        notification = notifications.first()
        assert notification.verb == "test_verb"
        assert notification.description == "test_description"
