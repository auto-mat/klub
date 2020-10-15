from django.test import TransactionTestCase

from interactions.models import InteractionType

from model_mommy import mommy


class AdministrativeUnitChangeSignalTest(TransactionTestCase):
    def setUp(self):
        self.unit1 = mommy.make('aklub.administrativeunit', name='unit1')
        self.unit2 = mommy.make('aklub.administrativeunit', name='unit2')

        self.user = mommy.make("aklub.userprofile")

    def test_preference_change_post_save(self):
        """
        Test signal if preference is created/removed after unit is added/removed to profile
        """
        self.assertEqual(self.user.preference_set.count(), 0)

        self.user.administrative_units.add(self.unit1)

        self.assertEqual(self.user.preference_set.count(), 1)
        self.assertCountEqual(list(self.user.preference_set.values_list('administrative_unit__name', flat=True)), ['unit1', ])
        self.assertEqual(self.user.is_active, True)

        self.user.administrative_units.add(self.unit2)

        self.assertEqual(self.user.preference_set.count(), 2)
        self.assertCountEqual(list(self.user.preference_set.values_list('administrative_unit__name', flat=True)), ['unit1', 'unit2'])
        self.assertEqual(self.user.is_active, True)
        self.user.administrative_units.remove(self.unit1)

        self.assertEqual(self.user.preference_set.count(), 1)
        self.assertCountEqual(list(self.user.preference_set.values_list('administrative_unit__name', flat=True)), ['unit2', ])
        self.assertEqual(self.user.is_active, True)

        self.user.administrative_units.remove(self.unit2)
        self.assertEqual(self.user.preference_set.count(), 0)
        self.assertEqual(self.user.is_active, False)

    def test_interaciton_change_post_save(self):
        """
        Test signal if preference is created/removed after unit is added/removed to profile
        """
        self.inter_add = InteractionType.objects.get(slug='administrative_unit_added')
        self.inter_remove = InteractionType.objects.get(slug='administrative_unit_removed')

        self.assertEqual(self.user.interaction_set.count(), 0)

        self.user.administrative_units.add(self.unit1)

        self.assertEqual(self.user.interaction_set.count(), 1)
        self.assertEqual(self.user.interaction_set.first().type, self.inter_add)
        self.assertEqual(self.user.interaction_set.first().administrative_unit, self.unit1)

        self.user.administrative_units.remove(self.unit1)

        self.assertEqual(self.user.interaction_set.count(), 2)
        self.assertEqual(self.user.interaction_set.last().type, self.inter_remove)
        self.assertEqual(self.user.interaction_set.last().administrative_unit, self.unit1)
