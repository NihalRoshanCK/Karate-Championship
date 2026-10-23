from django.db import migrations

GENDERS = [('M', 'Male'), ('F', 'Female')]

COLOUR_GROUPS = {
    'White': 'White, Yellow & Orange',
    'Yellow': 'White, Yellow & Orange',
    'Orange': 'White, Yellow & Orange',
    'Blue': 'Blue, Green & Purple',
    'Green': 'Blue, Green & Purple',
    'Purple': 'Blue, Green & Purple',
    'Brown': 'Brown',
}

SENIOR_WEIGHTS = [50, 55, 60, 65, 70, 75]

# The rules that used to be hardcoded in the candidate serializer.
# Weight lists are the upper limits; the last class is the open "+" class.
BELT_TYPES = [
    {
        'name': 'Colour Belt',
        'colours': ['White', 'Yellow', 'Orange', 'Green', 'Blue', 'Purple', 'Brown'],
        'age_categories': [
            ('Mini Sub Junior', 5, 9, [20, 25]),
            ('Sub Junior', 10, 13, [30, 35, 40, 45]),
            ('Cadet', 14, 15, [45, 50, 55, 60]),
            ('Junior', 16, 17, [50, 55, 60, 65]),
            ('Senior Below 21', 18, 21, SENIOR_WEIGHTS),
            ('Senior Above 21', 22, None, SENIOR_WEIGHTS),
        ],
    },
    {
        'name': 'Black Belt',
        'colours': ['Black'],
        'age_categories': [
            ('Sub Junior', 0, 13, [30, 35, 40, 45]),
            ('Cadet', 14, 15, [45, 50, 55, 60, 65]),
            ('Junior', 16, 17, [50, 55, 60, 65]),
            ('Senior Below 21', 18, 21, SENIOR_WEIGHTS),
            ('Senior Above 21', 22, None, SENIOR_WEIGHTS),
        ],
    },
]

PRICES = [('kata', 1000), ('kumite', 1000), ('both', 1500)]


def seed(apps, schema_editor):
    Gender = apps.get_model('Home', 'Gender')
    BeltType = apps.get_model('Home', 'BeltType')
    BeltColour = apps.get_model('Home', 'BeltColour')
    AgeCategory = apps.get_model('Home', 'AgeCategory')
    WeightCategory = apps.get_model('Home', 'WeightCategory')
    EventPrice = apps.get_model('Home', 'EventPrice')

    for order, (code, label) in enumerate(GENDERS):
        Gender.objects.create(code=code, label=label, order=order)

    for belt_order, config in enumerate(BELT_TYPES):
        belt_type = BeltType.objects.create(name=config['name'], order=belt_order)
        for order, colour in enumerate(config['colours']):
            BeltColour.objects.create(
                belt_type=belt_type, name=colour, order=order, filter_group=COLOUR_GROUPS.get(colour, ''),
            )
        for order, (name, min_age, max_age, limits) in enumerate(config['age_categories']):
            age_category = AgeCategory.objects.create(
                belt_type=belt_type, name=name, min_age=min_age, max_age=max_age, order=order,
            )
            for limit in limits:
                WeightCategory.objects.create(age_category=age_category, label=f'Kumite -{limit} Kg', max_weight=limit)
            WeightCategory.objects.create(age_category=age_category, label=f'Kumite +{limits[-1]} Kg', max_weight=None)

    for events, price in PRICES:
        EventPrice.objects.create(events=events, price=price)


def unseed(apps, schema_editor):
    for model in ['EventPrice', 'WeightCategory', 'AgeCategory', 'BeltColour', 'BeltType', 'Gender']:
        apps.get_model('Home', model).objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0003_championship_rules'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
