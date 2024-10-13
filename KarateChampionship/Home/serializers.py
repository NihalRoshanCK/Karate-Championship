from rest_framework import serializers
from .models import Club, Candidate
from Home.utilities import sent_users_mail
from rest_framework.exceptions import ValidationError
from django.db import transaction


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = '__all__'

    def create(self, validated_data):
        # Perform calculations
        instance = Candidate(**validated_data)
        instance.entry_fee = self.calculate_entry_fee(instance)
        instance.category = self.calculate_category(instance)
        instance.chest_no=self.assign_chest_no(instance)
        if instance.kumite:
            instance.weight_category = self.calculate_weight_category(instance)
        instance.club.no_of_candidate += 1
        instance.club.save()

        self.update_club_fees(instance)
        # Save the instance
        instance.save()
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
           
    def calculate_entry_fee(self, candidate):
        if (candidate.kata and (candidate.kumite == False)) or (candidate.kumite and (candidate.kata == False)):
            return 1000
        else:
            return 1500

    def calculate_category(self, candidate):
        belt_color = candidate.belt_color
        age = candidate.age

        age_category = {
            'Colour Belt': {
                (5, 9): 'Mini Sub Junior',
                (10, 13): 'Sub Junior',
                (14, 15): 'Cadet',
                (16, 17): 'Junior',
                (18, 21): 'Senior Below 21',
                (22, float('inf')): 'Senior Above 21'
            },
            'Black Belt': {
                (0, 12): 'Sub Junior',
                (13, 15): 'Cadet',
                (16, 17): 'Junior',
                (18, 21): 'Senior Below 21',
                (22, float('inf')): 'Senior Above 21'
            }
        }
        if belt_color in age_category:
            for age_range, group in age_category[belt_color].items():
                if age_range[0] <= age <= age_range[1]:
                    return group
            return ValidationError('Age group not found')  # Default if age does not fit into any range
        else:
            return ValidationError('Invalid belt color')
       

    def calculate_weight_category(self, candidate):
        if candidate.category and candidate.kumite:

            if candidate.belt_color == 'Colour Belt':
                if candidate.category == 'Mini Sub Junior':
                    if abs(candidate.weight) <= 20:
                        return 'Kumite -20 Kg'
                    elif 21 <= abs(candidate.weight) <= 25:
                        return 'Kumite -25 Kg'
                    else:
                        return 'Kumite +25 Kg'
                elif candidate.category=='Sub Junior':
                    if abs(candidate.weight)<=30:
                        return 'Kumite -30 Kg'
                    elif 30<abs(candidate.weight)<=35:
                        return 'Kumite -35 Kg'
                    elif 36<=abs(candidate.weight)<=40:
                        return 'Kumite -40 Kg'
                    elif 41<=abs(candidate.weight)<=45:
                        return 'Kumite -45 Kg'
                    else:
                        return 'Kumite +45 Kg'
                elif candidate.category=='Cadet':
                    if abs(candidate.weight)<=45:
                        return 'Kumite -45 Kg'
                    elif 46<=abs(candidate.weight)<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=abs(candidate.weight)<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=abs(candidate.weight)<=60:
                        return 'Kumite -60 Kg'
                    else:
                        return 'Kumite +60 Kg'
                elif candidate.category=='Junior':
                    if abs(candidate.weight)<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=abs(candidate.weight)<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=abs(candidate.weight)<=60:
                        return 'Kumite -60 Kg'
                    elif 61<=abs(candidate.weight)<=65:
                        return 'Kumite -65 Kg'
                    else:
                        return 'Kumite +65 Kg'
                else:
                    if candidate.weight<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=abs(candidate.weight)<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=abs(candidate.weight)<=60:
                        return 'Kumite -60 Kg'
                    elif 61<=abs(candidate.weight)<=65:
                        return 'Kumite -65 Kg'
                    elif 66<=abs(candidate.weight)<=70:
                        return 'Kumite -70 Kg'
                    elif 71<=abs(candidate.weight)<=75:
                        return 'Kumite -75 Kg'
                    else:
                        return 'Kumite +75 Kg'
            else:
                if candidate.category=='Sub Junior':
                    if abs(candidate.weight)<=30:
                        return 'Kumite -30 Kg'
                    elif 31<=abs(candidate.weight)<=35:
                        return 'Kumite -35 Kg'
                    elif 36<=abs(candidate.weight)<=40:
                        return 'Kumite -40 Kg'
                    elif 41<=abs(candidate.weight)<=45:
                        return 'Kumite -45 Kg'
                    else:
                        return 'Kumite +45 Kg'
                elif candidate.category=='Cadet':
                    if candidate.weight<=45:
                        return 'Kumite -45 Kg'
                    elif 46<=abs(candidate.weight)<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=abs(candidate.weight)<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=abs(candidate.weight)<=60:
                        return 'Kumite -60 Kg'
                    elif 61<=abs(candidate.weight)<=65:
                        return 'Kumite -65 Kg'
                    else:
                        return 'Kumite +65 Kg'
                elif candidate.category=='Junior':
                    if abs(candidate.weight)<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=abs(candidate.weight)<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=abs(candidate.weight)<=60:
                        return 'Kumite -60 Kg'
                    elif 61<=abs(candidate.weight)<=65:
                        return 'Kumite -65 Kg'
                    else:
                        return 'Kumite +65 Kg'
                else:
                    if candidate.weight<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=abs(candidate.weight)<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=abs(candidate.weight)<=60:
                        return 'Kumite -60 Kg'
                    elif 61<=abs(candidate.weight)<=65:
                        return 'Kumite -65 Kg'
                    elif 66<=abs(candidate.weight)<=70:
                        return 'Kumite -70 Kg'
                    elif 71<=abs(candidate.weight)<=75:
                        return 'Kumite -75 Kg'
                    else:
                        return 'Kumite +75 Kg'
                    
        return None
    
    def update_club_fees(self, candidate):
        # Increment the fees in the associated Club
        candidate.club.fees += candidate.entry_fee
        candidate.club.save()


    def update(self, instance, validated_data):
        # Check if kata or kumite fields are updated
        kata_updated = validated_data.get('kata', instance.kata)
        kumite_updated = validated_data.get('kumite', instance.kumite)

        old_entry_fee = instance.entry_fee

        if (kata_updated and not kumite_updated) or (kumite_updated and not kata_updated):
            new_entry_fee = 1000
        else:
            new_entry_fee = 1500

        # Update entry fee
        instance.entry_fee = new_entry_fee

        # Update club fees based on the difference in entry fees
        kata=instance.kata
        kumita=instance.kumite
        self.update_club_fees_on_entry_fee_change(instance, new_entry_fee, old_entry_fee)
        instance.weight = validated_data.get('weight', instance.weight)
        instance.belt_color = validated_data.get('belt_color', instance.belt_color)
        instance.age = validated_data.get('age', instance.age)
        instance.name = validated_data.get('name', instance.name)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.kumite = validated_data.get('kumite', instance.kumite)
        instance.kata = validated_data.get('kata', instance.kata)
        instance.colours=validated_data.get('colours',instance.colours)
        instance.club=validated_data.get('club',instance.club)
        # Recalculate category and weight category
        instance.category = self.calculate_category(instance)
        if instance.kata!=kata or instance.kumite!=kumita:
            instance.chest_no=self.assign_chest_no(instance)

        instance.weight_category = self.calculate_weight_category(instance) 

        # Update other fields in the instance

        instance.save()

        return instance
    

    def update_club_fees_on_entry_fee_change(self, candidate, new_entry_fee, old_entry_fee):
        # Calculate the difference in entry fees
        fee_difference = new_entry_fee - old_entry_fee
        # Update club fees based on the difference
        candidate.club.fees += fee_difference
        candidate.club.save()


class ClubSerializer(serializers.ModelSerializer):

    class Meta:
        model = Club
        fields = ['email','coach_name', 'name', 'phone', 'fees', 'password' , 'id','is_paid','no_of_candidate']
        extra_kwargs = {'password': {'write_only': True}}

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
                content = f'Dear {instance.coach_name},\n\nWe are pleased to inform you that your payment for the championship registration has been successfully received. Wishing you the utmost success in the upcoming championship.\n\nBest regards,\nOrganization committee,\nNATIONAL KENYURYU KARATE CHAMPIONSHIP,\nAIKO EVENTS'
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