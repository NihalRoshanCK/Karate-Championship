# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.cache import cache
from django.core.exceptions import ValidationError


class CustomClubManager(BaseUserManager):
    def create_user(self, email,name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not name:
            raise ValueError('The name field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,name=name, **extra_fields)
        user.set_password(password) # Password hashing is done here
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Club(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name=models.CharField(max_length=150)
    coach_name=models.CharField()
    phone=models.BigIntegerField()
    fees = models.IntegerField(default=0)
    is_paid = models.BooleanField(default=False)
    no_of_candidate=models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = CustomClubManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    def __str__(self):
        return self.email


class Candidate(models.Model):
    # Gender, belt type, colour and categories are configured in the tables
    # below and validated by Home.rules; the chosen values are stored as text
    # so existing registrations keep their values when the rules change later.
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    gender = models.CharField(max_length=20)
    belt_color = models.CharField(max_length=80)
    weight = models.FloatField()
    kata = models.BooleanField(default=False)
    kumite = models.BooleanField(default=False)
    category = models.CharField(max_length=50, blank=True, null=True)
    weight_category = models.CharField(max_length=250, blank=True, null=True)
    entry_fee=models.IntegerField(blank=True, null=True)
    chest_no=models.CharField(null=True)
    colours = models.CharField(max_length=50)

    
    def __str__(self):
        return self.name
class Spacial(models.Model):
    FAMILY_KATA = 'FAMILY KATA'
    BLACK_BELT_TEAM_KATA  = 'BLACK BELT TEAM KATA'
    Events = [
        (FAMILY_KATA , 'FAMILY KATA'),
        (BLACK_BELT_TEAM_KATA, 'BLACK BELT TEAM KATA'),
    ]
    club= models.ForeignKey(Club, on_delete=models.CASCADE)
    candidate = models.ManyToManyField(Candidate)
    category = models.CharField(choices=Events)

#   TAKESHI START

class SiteSettings(models.Model):
    CACHE_KEY = 'site_settings'

    championship_name = models.CharField(max_length=255, default='CHIKUBUKAI NATIONAL OPEN KARATE CHAMPIONSHIP 2025')
    logo = models.ImageField(upload_to='branding/', blank=True, null=True)
    sidebar_logo = models.ImageField(upload_to='branding/', blank=True, null=True)
    login_image = models.ImageField(upload_to='branding/', blank=True, null=True)
    favicon = models.ImageField(upload_to='branding/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site settings'
        verbose_name_plural = 'Site settings'

    def __str__(self):
        return self.championship_name

    def save(self, *args, **kwargs):
        # Only one row is ever used
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(self.CACHE_KEY)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete(self.CACHE_KEY)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj



# Championship rules, editable from the Django admin

class Gender(models.Model):
    code = models.CharField(max_length=20, unique=True, help_text='Stored on the candidate, e.g. M')
    label = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.label


class BeltType(models.Model):
    name = models.CharField(max_length=80, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class BeltColour(models.Model):
    belt_type = models.ForeignKey(BeltType, on_delete=models.CASCADE, related_name='colours')
    name = models.CharField(max_length=50)
    filter_group = models.CharField(
        max_length=100, blank=True,
        help_text='Colours with the same group are filtered together on the admin dashboard, e.g. "White, Yellow & Orange". Leave empty to use the colour name.',
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        constraints = [models.UniqueConstraint(fields=['belt_type', 'name'], name='unique_colour_per_belt_type')]

    def __str__(self):
        return f'{self.belt_type} - {self.name}'


class AgeCategory(models.Model):
    belt_type = models.ForeignKey(BeltType, on_delete=models.CASCADE, related_name='age_categories')
    name = models.CharField(max_length=50)
    min_age = models.PositiveIntegerField()
    max_age = models.PositiveIntegerField(blank=True, null=True, help_text='Leave empty for no upper limit')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'min_age']
        verbose_name_plural = 'Age categories'
        constraints = [models.UniqueConstraint(fields=['belt_type', 'name'], name='unique_age_category_per_belt_type')]

    def __str__(self):
        return f'{self.belt_type} - {self.name}'

    def clean(self):
        # Overlaps with the other categories are checked by the admin forms,
        # which see every row being saved together
        if self.max_age is not None and self.min_age is not None and self.max_age < self.min_age:
            raise ValidationError({'max_age': 'Max age must be greater than or equal to min age.'})


class WeightCategory(models.Model):
    age_category = models.ForeignKey(AgeCategory, on_delete=models.CASCADE, related_name='weight_categories')
    gender = models.ForeignKey(
        Gender, on_delete=models.CASCADE, blank=True, null=True,
        help_text='Leave empty to use this class for every gender without its own classes',
    )
    label = models.CharField(max_length=100, help_text='e.g. Kumite -25 Kg')
    max_weight = models.FloatField(
        blank=True, null=True,
        help_text='Upper limit in Kg (inclusive). The class starts just above the previous limit. Leave empty for the open (+) class.',
    )

    class Meta:
        ordering = [models.F('max_weight').asc(nulls_last=True)]
        verbose_name_plural = 'Weight categories'

    def __str__(self):
        return f'{self.age_category} - {self.label}'



class EventPrice(models.Model):
    KATA = 'kata'
    KUMITE = 'kumite'
    BOTH = 'both'
    EVENT_CHOICES = [
        (KATA, 'Kata only'),
        (KUMITE, 'Kumite only'),
        (BOTH, 'Kata and Kumite'),
    ]

    events = models.CharField(max_length=10, choices=EVENT_CHOICES)
    price = models.PositiveIntegerField()
    belt_type = models.ForeignKey(
        BeltType, on_delete=models.CASCADE, blank=True, null=True,
        help_text='Optional: only for this belt type',
    )
    age_category = models.ForeignKey(
        AgeCategory, on_delete=models.CASCADE, blank=True, null=True,
        help_text='Optional: only for this age category',
    )

    class Meta:
        ordering = ['events', 'id']

    def __str__(self):
        scope = self.age_category or self.belt_type or 'everyone'
        return f'{self.get_events_display()} - {self.price} ({scope})'

    def clean(self):
        if self.age_category_id and self.belt_type_id and self.age_category.belt_type_id != self.belt_type_id:
            raise ValidationError('The age category belongs to a different belt type.')
        duplicates = EventPrice.objects.filter(
            events=self.events, belt_type_id=self.belt_type_id, age_category_id=self.age_category_id,
        ).exclude(pk=self.pk)
        if duplicates.exists():
            raise ValidationError('A price for these events and this scope already exists.')
