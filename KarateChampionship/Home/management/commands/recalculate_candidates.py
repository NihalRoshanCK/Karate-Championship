from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Sum
from rest_framework.exceptions import ValidationError

from Home import rules
from Home.models import Candidate, Club

FIELDS = ['colours', 'category', 'weight_category', 'entry_fee']


class Command(BaseCommand):
    help = (
        'Compare existing candidates and club totals with the current championship rules. '
        'Only reports by default; pass --apply to save the changes.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Save the recalculated values')

    def handle(self, *args, apply=False, **options):
        changed, failed = [], []
        for candidate in Candidate.objects.select_related('club').order_by('id'):
            try:
                result = rules.evaluate(
                    gender=candidate.gender, belt_color=candidate.belt_color, colours=candidate.colours,
                    age=candidate.age, weight=candidate.weight, kata=candidate.kata, kumite=candidate.kumite,
                )
            except ValidationError as error:
                detail = error.detail
                messages = detail.values() if isinstance(detail, dict) else [detail]
                failed.append((candidate, '; '.join(str(m[0] if isinstance(m, list) else m) for m in messages)))
                continue
            diff = {f: (getattr(candidate, f), result[f]) for f in FIELDS if getattr(candidate, f) != result[f]}
            if diff:
                changed.append((candidate, diff))

        totals = {
            row['club']: row
            for row in Candidate.objects.values('club').annotate(fees=Sum('entry_fee'), count=Count('id'))
        }
        clubs = []
        for club in Club.objects.order_by('id'):
            row = totals.get(club.id, {})
            real = (row.get('fees') or 0, row.get('count') or 0)
            if (club.fees, club.no_of_candidate) != real:
                clubs.append((club, (club.fees, club.no_of_candidate), real))

        total = Candidate.objects.count()
        self.stdout.write(f'{total} candidate(s) checked.')
        for candidate, diff in changed:
            changes = ', '.join(f'{field}: {old!r} -> {new!r}' for field, (old, new) in diff.items())
            self.stdout.write(f'  CHANGE  #{candidate.id} {candidate.name} ({candidate.club.name}): {changes}')
        for candidate, error in failed:
            self.stdout.write(self.style.ERROR(
                f'  INVALID #{candidate.id} {candidate.name} ({candidate.club.name}): {error} - fix this candidate by hand'
            ))
        for club, stored, real in clubs:
            self.stdout.write(
                f'  TOTALS  club #{club.id} {club.name}: stored fees/count {stored} -> actual {real}'
            )

        if not (changed or clubs):
            self.stdout.write(self.style.SUCCESS('Nothing to update.' + (' (Some candidates are invalid, see above.)' if failed else '')))
            return
        if not apply:
            self.stdout.write(self.style.WARNING(
                f'{len(changed)} candidate(s) and {len(clubs)} club total(s) would change. Run again with --apply to save.'
            ))
            return
        with transaction.atomic():
            rules.recalculate_candidates([candidate for candidate, _ in changed])
            rules.rebuild_club_totals([club.id for club in Club.objects.all()])
        self.stdout.write(self.style.SUCCESS(f'Updated {len(changed)} candidate(s) and all club totals.'))
