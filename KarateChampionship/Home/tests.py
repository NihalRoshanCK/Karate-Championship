from django.core.cache import cache
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from . import rules
from .models import AgeCategory, BeltType, Candidate, Club, EventPrice, Gender, WeightCategory


def evaluate(**overrides):
    details = dict(gender='M', belt_color='Colour Belt', colours='Yellow', age=12, weight=33, kata=True, kumite=True)
    details.update(overrides)
    return rules.evaluate(**details)


class SeededRulesTests(TestCase):
    """The seed migration must reproduce the rules that used to be hardcoded."""

    def test_age_categories(self):
        self.assertEqual(evaluate(age=5)['category'], 'Mini Sub Junior')
        self.assertEqual(evaluate(age=13)['category'], 'Sub Junior')
        self.assertEqual(evaluate(age=21)['category'], 'Senior Below 21')
        self.assertEqual(evaluate(age=60)['category'], 'Senior Above 21')
        self.assertEqual(evaluate(belt_color='Black Belt', colours='Black', age=3)['category'], 'Sub Junior')

    def test_age_without_category_is_rejected(self):
        with self.assertRaises(ValidationError):
            evaluate(age=4)

    def test_weight_categories(self):
        self.assertEqual(evaluate(age=7, weight=20)['weight_category'], 'Kumite -20 Kg')
        self.assertEqual(evaluate(age=7, weight=25)['weight_category'], 'Kumite -25 Kg')
        self.assertEqual(evaluate(age=7, weight=26)['weight_category'], 'Kumite +25 Kg')
        self.assertEqual(evaluate(belt_color='Black Belt', colours='Black', age=15, weight=62)['weight_category'], 'Kumite -65 Kg')
        self.assertEqual(evaluate(age=15, weight=62)['weight_category'], 'Kumite +60 Kg')

    def test_fractional_weight_falls_in_next_class(self):
        # Used to fall through to the open class
        self.assertEqual(evaluate(age=7, weight=20.5)['weight_category'], 'Kumite -25 Kg')

    def test_no_weight_category_without_kumite(self):
        self.assertIsNone(evaluate(kumite=False)['weight_category'])

    def test_fees(self):
        self.assertEqual(evaluate(kumite=False)['entry_fee'], 1000)
        self.assertEqual(evaluate(kata=False)['entry_fee'], 1000)
        self.assertEqual(evaluate()['entry_fee'], 1500)

    def test_single_colour_belt_fills_colour(self):
        self.assertEqual(evaluate(belt_color='Black Belt', colours='')['colours'], 'Black')

    def test_invalid_values_are_rejected(self):
        for overrides in [{'gender': 'X'}, {'belt_color': 'Red Belt'}, {'colours': 'Black'}, {'kata': False, 'kumite': False}]:
            with self.assertRaises(ValidationError):
                evaluate(**overrides)


class ConfiguredRulesTests(TestCase):
    def test_most_specific_price_wins(self):
        cadet = AgeCategory.objects.get(belt_type__name='Colour Belt', name='Cadet')
        EventPrice.objects.create(events='both', price=1200, belt_type=cadet.belt_type)
        EventPrice.objects.create(events='both', price=900, age_category=cadet)
        self.assertEqual(evaluate(age=15)['entry_fee'], 900)
        self.assertEqual(evaluate(age=12)['entry_fee'], 1200)
        self.assertEqual(evaluate(belt_color='Black Belt', colours='Black')['entry_fee'], 1500)

    def test_gender_specific_weight_classes(self):
        female = Gender.objects.get(code='F')
        mini = AgeCategory.objects.get(belt_type__name='Colour Belt', name='Mini Sub Junior')
        WeightCategory.objects.create(age_category=mini, gender=female, label='Girls -22 Kg', max_weight=22)
        WeightCategory.objects.create(age_category=mini, gender=female, label='Girls +22 Kg')
        self.assertEqual(evaluate(gender='F', age=7, weight=21)['weight_category'], 'Girls -22 Kg')
        self.assertEqual(evaluate(gender='M', age=7, weight=21)['weight_category'], 'Kumite -25 Kg')

    def test_config_cache_is_cleared_on_change(self):
        cache.clear()
        before = rules.get_config()
        Gender.objects.create(code='O', label='Other')
        after = rules.get_config()
        self.assertNotEqual(before['version'], after['version'])
        self.assertIn('O', [g['code'] for g in after['genders']])


class CandidateApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.club = Club.objects.create_user(email='club@example.com', name='Club', password='pw', phone=1, coach_name='c')

    def payload(self, **overrides):
        data = dict(name='Kid', club=self.club.id, gender='M', belt_color='Colour Belt', colours='Blue',
                    age=12, weight=33, kata=True, kumite=False)
        data.update(overrides)
        return data

    def test_create_and_update_keep_club_totals(self):
        response = self.client.post('/api/candidates/', self.payload(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['entry_fee'], 1000)
        self.club.refresh_from_db()
        self.assertEqual((self.club.fees, self.club.no_of_candidate), (1000, 1))

        candidate_id = response.data['id']
        response = self.client.patch(f'/api/candidates/{candidate_id}/', {'kumite': True}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['weight_category'], 'Kumite -35 Kg')
        self.club.refresh_from_db()
        self.assertEqual(self.club.fees, 1500)

        self.client.delete(f'/api/candidates/{candidate_id}/')
        self.club.refresh_from_db()
        self.assertEqual((self.club.fees, self.club.no_of_candidate), (0, 0))

    def test_client_cannot_set_fee(self):
        response = self.client.post('/api/candidates/', self.payload(entry_fee=1), format='json')
        self.assertEqual(response.data['entry_fee'], 1000)

    def test_invalid_age_returns_400(self):
        response = self.client.post('/api/candidates/', self.payload(age=3), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('age', response.data)

    def test_recalculate_after_price_change(self):
        self.client.post('/api/candidates/', self.payload(), format='json')
        EventPrice.objects.filter(events='kata', belt_type=None, age_category=None).update(price=800)
        updated, errors = rules.recalculate_candidates(Candidate.objects.all())
        self.assertEqual((updated, errors), (1, []))
        self.club.refresh_from_db()
        self.assertEqual(self.club.fees, 800)

    def test_config_endpoint(self):
        response = self.client.get('/api/championship-config/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([b['name'] for b in response.data['belt_types']], ['Colour Belt', 'Black Belt'])
        again = self.client.get('/api/championship-config/', HTTP_IF_NONE_MATCH=response['ETag'])
        self.assertEqual(again.status_code, 304)
