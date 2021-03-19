from django.test import TestCase

from model_mommy import mommy

from ..utils import send_notification_to_is_staff_members


class CreateNotificationTest(TestCase):
    """
    Test every module where notification is created (and how is created)
    """
    def setUp(self):
        self.unit = mommy.make('aklub.administrativeunit', name='test_unit')
        self.user = mommy.make('aklub.UserProfile', administrated_units=[self.unit, ], is_superuser=True, is_staff=True)

    def test_send_notification_to_is_staff_members(self):
        send_notification_to_is_staff_members(self.unit, "test_verb", "test_description")
        notifications = self.user.notifications.all()
        self.assertEqual(notifications.count(), 1)
        notification = notifications.first()
        self.assertEqual(notification.verb, "test_verb")
        self.assertEqual(notification.description, "test_description")
