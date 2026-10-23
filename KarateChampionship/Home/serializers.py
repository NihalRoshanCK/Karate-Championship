from rest_framework import serializers
from .models import Club, Candidate, SiteSettings
from Home.utilities import sent_users_mail
from Home import rules
from rest_framework.exceptions import ValidationError
from django.db import transaction


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = '__all__'
        # Worked out from the championship rules, never taken from the client
        read_only_fields = ['category', 'weight_category', 'entry_fee', 'chest_no']
        extra_kwargs = {'colours': {'required': False, 'allow_blank': True}}

    def validate(self, attrs):
        def value(field):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field, None)

        attrs.update(rules.evaluate(
            gender=value('gender'),
            belt_color=value('belt_color'),
            colours=value('colours'),
            age=value('age'),
            weight=value('weight'),
            kata=bool(value('kata')),
            kumite=bool(value('kumite')),
        ))
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        instance = Candidate(**validated_data)
        instance.chest_no = self.assign_chest_no(instance)
        instance.save()
        rules.rebuild_club_totals([instance.club_id])
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        old_club_id = instance.club_id
        old_events = (instance.kata, instance.kumite)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if (instance.kata, instance.kumite) != old_events:
            instance.chest_no = self.assign_chest_no(instance)
        instance.save()
        rules.rebuild_club_totals({old_club_id, instance.club_id})
        return instance

    def assign_chest_no(self,candidate):
        student=Candidate.objects.filter(kata=candidate.kata,kumite=candidate.kumite).last()
        if student is None:
            if candidate.kata and candidate.kumite:
                return "KK0001"
            elif candidate.kata:
                return "KA0001"
            else:
                return "KU0001"
        else:
            if candidate.kata and candidate.kumite:
                expression="KK"
            elif candidate.kata:
                expression="KA"
            else:
                expression="KU"
            return  f'{expression}{int(student.chest_no[2:6]) + 1:04d}'


class ClubSerializer(serializers.ModelSerializer):

    class Meta:
        model = Club
        fields = ['email','coach_name', 'name', 'phone', 'fees', 'password' , 'id','is_paid','no_of_candidate','is_staff']
        extra_kwargs = {'password': {'write_only': True}, 'is_staff': {'read_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        club = Club.objects.create(**validated_data)
        if password is not None:
            club.set_password(password)
            club.save()
        return club
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        candidates = CandidateSerializer(instance.candidate_set.all(), many=True).data
        sorted_candidates = self.sort_candidates(candidates)
        representation['candidates'] = sorted_candidates
        return representation
    
    def sort_candidates(self, candidates):
        # Sort the candidates based on whether they have kata and kumite, kata only, or kumite only
        sorted_candidates = sorted(candidates, key=lambda x: (
            not x['kumite'] and not x['kata'],  # Candidates having both kata and kumite
            not x['kumite'] and x['kata'],      # Candidates only having kata
            x['kumite'] and not x['kata']       # Candidates only having kumite
        ))
        return sorted_candidates
    
    def update(self, instance, validated_data):
        try:
            if validated_data.get("is_paid", False):
                title = 'Payment Received'
                content = f'Dear {instance.coach_name},\n\nWe are pleased to inform you that your payment for the championship registration has been successfully received. Wishing you the utmost success in the upcoming championship.\n\nBest regards,\nOrganization committee,\nAIKO EVENTS'
                sent_users_mail(instance.email, content, title)
                instance.save()
        except Exception as e:
            pass  
        return super().update(instance, validated_data)


class ClubStatisticsSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField()
    total_entry_fee = serializers.IntegerField()
    total_candidates = serializers.IntegerField()
    total_kumite_entry_fee = serializers.IntegerField()
    total_kumite_candidates = serializers.IntegerField()
    total_kata_entry_fee = serializers.IntegerField()
    total_kata_candidates = serializers.IntegerField()
    total_both_entry_fee = serializers.IntegerField()
    total_kumite_and_kata_candidates= serializers.IntegerField()

class SiteSettingsSerializer(serializers.ModelSerializer):
    IMAGE_FIELDS = ['logo', 'sidebar_logo', 'login_image', 'favicon']

    class Meta:
        model = SiteSettings
        fields = ['championship_name', 'logo', 'sidebar_logo', 'login_image', 'favicon', 'updated_at']
        read_only_fields = ['updated_at']

    def to_representation(self, instance):
        # Relative urls with a version suffix, so the result is cacheable and
        # browsers can keep the images until they are replaced
        version = int(instance.updated_at.timestamp() * 1000)
        representation = {
            'championship_name': instance.championship_name,
            'version': version,
        }
        for field in self.IMAGE_FIELDS:
            image = getattr(instance, field)
            representation[field] = f'{image.url}?v={version}' if image else None
        return representation
