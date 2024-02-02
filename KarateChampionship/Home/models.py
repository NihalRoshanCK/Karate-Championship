# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


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
    MALE = 'M'
    FEMALE = 'F'
    GENDER_CHOICES = [
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    ]

    COLOUR_BELT = 'Colour Belt'
    BLACK_BELT = 'Black Belt'
    BELT_CHOICES = [
        (COLOUR_BELT, 'Colour Belt'),
        (BLACK_BELT, 'Black Belt'),
    ]

    KUMITE = 'Kumite'
    KATA = 'Kata'
    
    WHITE = 'White'
    YELLOW = 'Yellow'
    ORANGE = 'Orange'
    GREEN = 'Green'
    BLUE = 'Blue'
    PURPLE = 'Purple'
    BROWN = 'Brown'
    BLACK = 'Black'
    COLOUR_CHOICES = [
        (WHITE, 'White'),
        (YELLOW, 'Yellow'),
        (ORANGE, 'Orange'),
        (GREEN, 'Green'),
        (BLUE, 'Blue'),
        (PURPLE, 'Purple'),
        (BROWN, 'Brown'),
        (BLACK, 'Black'),
    ]

    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    belt_color = models.CharField(max_length=20, choices=BELT_CHOICES)
    weight = models.FloatField()
    kata = models.BooleanField(default=False)
    kumite = models.BooleanField(default=False)
    category = models.CharField(max_length=20, blank=True, null=True)
    weight_category = models.CharField(max_length=20, blank=True, null=True)
    entry_fee=models.IntegerField(blank=True, null=True)
    colours = models.CharField(default=BLACK,max_length=20, choices=COLOUR_CHOICES)

    
    def __str__(self):
        return self.name

   