"""Championship rules: categories, weight classes and fees, read from the
configuration tables instead of being hardcoded."""
import hashlib
import json

from django.core.cache import cache
from django.db.models import Count, Sum
from rest_framework.exceptions import ValidationError

from .models import AgeCategory, BeltColour, BeltType, Candidate, Club, EventPrice, Gender, WeightCategory

CONFIG_CACHE_KEY = 'championship_config'
CONFIG_CACHE_TIMEOUT = 300


def events_key(kata, kumite):
    if kata and kumite:
        return EventPrice.BOTH
    if kata:
        return EventPrice.KATA
    if kumite:
        return EventPrice.KUMITE
    return None


def get_belt_type(name):
    belt_type = BeltType.objects.filter(name=name, is_active=True).first()
    if belt_type is None:
        raise ValidationError({'belt_color': f'"{name}" is not a valid belt type.'})
    return belt_type


def resolve_colour(belt_type, colour):
    colours = list(belt_type.colours.filter(is_active=True).values_list('name', flat=True))
    if not colour and len(colours) == 1:
        # Belt types with a single colour (e.g. Black Belt) don't ask for one
        return colours[0]
    if colour not in colours:
        raise ValidationError({'colours': f'"{colour}" is not a valid colour for {belt_type.name}.'})
    return colour


def get_age_category(belt_type, age):
    for age_category in belt_type.age_categories.all():
        if age_category.min_age <= age and (age_category.max_age is None or age <= age_category.max_age):
            return age_category
    raise ValidationError({'age': f'No {belt_type.name} age category for age {age}.'})


def get_weight_category(age_category, gender_code, weight):
    classes = list(age_category.weight_categories.select_related('gender'))
    # Gender specific classes win over the shared ones
    own = [c for c in classes if c.gender and c.gender.code == gender_code]
    classes = own or [c for c in classes if c.gender is None]
    if not classes:
        raise ValidationError({'weight': f'No weight classes configured for {age_category}.'})
    for weight_class in classes:  # ordered by max_weight, open class last
        if weight_class.max_weight is None or weight <= weight_class.max_weight:
            return weight_class.label
    raise ValidationError({'weight': f'No weight class in {age_category} for {weight} Kg.'})


def get_entry_fee(events, belt_type, age_category):
    prices = EventPrice.objects.filter(events=events)
    best, best_score = None, -1
    for price in prices:
        if price.belt_type_id not in (None, belt_type.id):
            continue
        if price.age_category_id not in (None, age_category.id):
            continue
        # The most specific price wins
        score = (2 if price.age_category_id else 0) + (1 if price.belt_type_id else 0)
        if score > best_score:
            best, best_score = price, score
    if best is None:
        raise ValidationError({'non_field_errors': [f'No price configured for {events}.']})
    return best.price


def evaluate(*, gender, belt_color, colours, age, weight, kata, kumite):
    """Validate a candidate's details and work out category, weight class and fee."""
    if not Gender.objects.filter(code=gender, is_active=True).exists():
        raise ValidationError({'gender': f'"{gender}" is not a valid gender.'})
    events = events_key(kata, kumite)
    if events is None:
        raise ValidationError({'non_field_errors': ['Select at least one event.']})
    belt_type = get_belt_type(belt_color)
    colour = resolve_colour(belt_type, colours)
    age_category = get_age_category(belt_type, age)
    return {
        'colours': colour,
        'category': age_category.name,
        'weight_category': get_weight_category(age_category, gender, weight) if kumite else None,
        'entry_fee': get_entry_fee(events, belt_type, age_category),
    }


def rebuild_club_totals(club_ids):
    """Recompute the stored fee and candidate counters from the real candidates."""
    totals = {
        row['club']: row
        for row in Candidate.objects.filter(club_id__in=club_ids)
        .values('club').annotate(fees=Sum('entry_fee'), count=Count('id'))
    }
    for club in Club.objects.filter(id__in=club_ids):
        row = totals.get(club.id, {})
        club.fees = row.get('fees') or 0
        club.no_of_candidate = row.get('count') or 0
        club.save(update_fields=['fees', 'no_of_candidate'])


def recalculate_candidates(candidates):
    """Apply the current rules to existing candidates. Returns (updated, errors)."""
    updated, errors, club_ids = 0, [], set()
    for candidate in candidates:
        try:
            result = evaluate(
                gender=candidate.gender, belt_color=candidate.belt_color, colours=candidate.colours,
                age=candidate.age, weight=candidate.weight, kata=candidate.kata, kumite=candidate.kumite,
            )
        except ValidationError as error:
            errors.append(f'{candidate.name} ({candidate.chest_no}): {error.detail}')
            continue
        for field, value in result.items():
            setattr(candidate, field, value)
        candidate.save(update_fields=list(result))
        club_ids.add(candidate.club_id)
        updated += 1
    rebuild_club_totals(club_ids)
    return updated, errors


def build_config():
    belt_types = []
    for belt_type in BeltType.objects.filter(is_active=True).prefetch_related(
        'colours', 'age_categories__weight_categories__gender',
    ):
        belt_types.append({
            'id': belt_type.id,
            'name': belt_type.name,
            'colours': [
                {'name': colour.name, 'filter_group': colour.filter_group or colour.name}
                for colour in belt_type.colours.all() if colour.is_active
            ],
            'age_categories': [
                {
                    'id': age_category.id,
                    'name': age_category.name,
                    'min_age': age_category.min_age,
                    'max_age': age_category.max_age,
                    'weight_categories': [
                        {
                            'label': weight_class.label,
                            'max_weight': weight_class.max_weight,
                            'gender': weight_class.gender.code if weight_class.gender else None,
                        }
                        for weight_class in age_category.weight_categories.all()
                    ],
                }
                for age_category in belt_type.age_categories.all()
            ],
        })
    data = {
        'genders': [
            {'code': gender.code, 'label': gender.label}
            for gender in Gender.objects.filter(is_active=True)
        ],
        'belt_types': belt_types,
        'prices': [
            {
                'events': price.events,
                'price': price.price,
                'belt_type': price.belt_type_id,
                'age_category': price.age_category_id,
            }
            for price in EventPrice.objects.all()
        ],
    }
    # Content based version, so every server process produces the same ETag
    data['version'] = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    return data


def get_config():
    data = cache.get(CONFIG_CACHE_KEY)
    if data is None:
        data = build_config()
        cache.set(CONFIG_CACHE_KEY, data, CONFIG_CACHE_TIMEOUT)
    return data


def clear_config_cache(**kwargs):
    cache.delete(CONFIG_CACHE_KEY)


CONFIG_MODELS = [Gender, BeltType, BeltColour, AgeCategory, WeightCategory, EventPrice]
