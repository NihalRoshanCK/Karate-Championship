from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, ModelForm
from .models import *
from . import rules

# Register your models here.


@admin.action(description='Recalculate categories & fees with the current rules')
def recalculate_selected(modeladmin, request, queryset):
    updated, errors = rules.recalculate_candidates(queryset)
    modeladmin.message_user(request, f'{updated} candidate(s) recalculated.', messages.SUCCESS)
    for error in errors:
        modeladmin.message_user(request, error, messages.ERROR)


@admin.action(description='Recalculate categories & fees of all candidates in these clubs')
def recalculate_clubs(modeladmin, request, queryset):
    recalculate_selected(modeladmin, request, Candidate.objects.filter(club__in=queryset))


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'chest_no', 'club', 'belt_color', 'colours', 'category', 'weight_category', 'entry_fee']
    list_filter = ['belt_color', 'category', 'gender', 'kata', 'kumite']
    search_fields = ['name', 'chest_no']
    actions = [recalculate_selected]


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'coach_name', 'no_of_candidate', 'fees', 'is_paid']
    search_fields = ['name', 'email']
    actions = [recalculate_clubs]


def age_overlap(rows):
    """rows: (name, min_age, max_age); returns the first overlapping pair."""
    ordered = sorted(rows, key=lambda row: row[1])
    for previous, current in zip(ordered, ordered[1:]):
        if previous[2] is None or current[1] <= previous[2]:
            return previous[0], current[0]
    return None


class AgeCategoryFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        rows = [
            (form.cleaned_data['name'], form.cleaned_data['min_age'], form.cleaned_data.get('max_age'))
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE')
        ]
        overlap = age_overlap(rows)
        if overlap:
            raise ValidationError(f'Age ranges of "{overlap[0]}" and "{overlap[1]}" overlap.')


class AgeCategoryForm(ModelForm):
    class Meta:
        model = AgeCategory
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        belt_type = cleaned.get('belt_type')
        if belt_type and cleaned.get('min_age') is not None:
            others = AgeCategory.objects.filter(belt_type=belt_type).exclude(pk=self.instance.pk)
            rows = [(o.name, o.min_age, o.max_age) for o in others]
            rows.append((cleaned.get('name'), cleaned['min_age'], cleaned.get('max_age')))
            overlap = age_overlap(rows)
            if overlap:
                raise ValidationError(f'Age ranges of "{overlap[0]}" and "{overlap[1]}" overlap.')
        return cleaned


class WeightCategoryFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        seen = set()
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            key = (form.cleaned_data.get('gender'), form.cleaned_data.get('max_weight'))
            if key in seen:
                gender = key[0] or 'all genders'
                limit = f'{key[1]} Kg' if key[1] is not None else 'the open class'
                raise ValidationError(f'Two weight classes for {gender} have the same limit ({limit}).')
            seen.add(key)


class BeltColourInline(admin.TabularInline):
    model = BeltColour
    extra = 0


class AgeCategoryInline(admin.TabularInline):
    model = AgeCategory
    formset = AgeCategoryFormSet
    extra = 0
    show_change_link = True


class WeightCategoryInline(admin.TabularInline):
    model = WeightCategory
    formset = WeightCategoryFormSet
    extra = 0


@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    list_display = ['label', 'code', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(BeltType)
class BeltTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    inlines = [BeltColourInline, AgeCategoryInline]


@admin.register(AgeCategory)
class AgeCategoryAdmin(admin.ModelAdmin):
    form = AgeCategoryForm
    list_display = ['name', 'belt_type', 'min_age', 'max_age', 'order']
    list_filter = ['belt_type']
    inlines = [WeightCategoryInline]


@admin.register(EventPrice)
class EventPriceAdmin(admin.ModelAdmin):
    list_display = ['events', 'price', 'belt_type', 'age_category']
    list_editable = ['price']
    list_filter = ['events', 'belt_type']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
