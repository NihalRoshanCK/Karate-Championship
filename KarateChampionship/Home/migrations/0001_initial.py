# Generated by Django 5.0.1 on 2024-01-30 12:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Club',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('name', models.CharField(max_length=150)),
                ('coach_name', models.CharField(max_length=15)),
                ('phone', models.BigIntegerField()),
                ('fees', models.IntegerField(default=0)),
                ('is_paid', models.BooleanField(default=False)),
                ('no_of_candidate', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('age', models.IntegerField()),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female')], max_length=1)),
                ('belt_color', models.CharField(choices=[('Colour Belt', 'Colour Belt'), ('Black Belt', 'Black Belt')], max_length=20)),
                ('weight', models.FloatField()),
                ('kata', models.BooleanField(default=False)),
                ('kumite', models.BooleanField(default=False)),
                ('category', models.CharField(blank=True, max_length=20, null=True)),
                ('weight_category', models.CharField(blank=True, max_length=20, null=True)),
                ('entry_fee', models.IntegerField(blank=True, null=True)),
                ('colours', models.CharField(choices=[('White', 'White'), ('Yellow', 'Yellow'), ('Orange', 'Orange'), ('Green', 'Green'), ('Blue', 'Blue'), ('Purple', 'Purple'), ('Brown', 'Brown'), ('Black', 'Black')], default='Black', max_length=20)),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
