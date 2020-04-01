from django.test import TransactionTestCase

from model_mommy import mommy

from ..models import UserProfile


class AdministrativeUnitChangeSignalTest(TransactionTestCase):
    def test_if_preference_is_changed(self):
        """
        Test signal if preference is created/removed after unit is added/removed to profile
        """
        unit1 = mommy.make('aklub.administrativeunit', name='unit1')
        unit2 = mommy.make('aklub.administrativeunit', name='unit2')
        mommy.make("aklub.userprofile", id=11, administrative_units=[unit1, ])

        user = UserProfile.objects.get(id=11)
        self.assertEqual(user.preference_set.count(), 1)
        self.assertListEqual(list(user.preference_set.values_list('administrative_unit__name', flat=True)), ['unit1', ])
        self.assertEqual(user.is_active, True)

        user.administrative_units.add(unit2)

        self.assertEqual(user.preference_set.count(), 2)
        self.assertListEqual(list(user.preference_set.values_list('administrative_unit__name', flat=True)), ['unit1', 'unit2'])
        self.assertEqual(user.is_active, True)

        user.administrative_units.remove(unit1)

        self.assertEqual(user.preference_set.count(), 1)
        self.assertListEqual(list(user.preference_set.values_list('administrative_unit__name', flat=True)), ['unit2', ])
        self.assertEqual(user.is_active, True)

        user.administrative_units.remove(unit2)
        self.assertEqual(user.preference_set.count(), 0)
        self.assertEqual(user.is_active, False)
