from rest_framework import serializers
from .models import Club, Candidate
from Home.utilities import sent_users_mail
from rest_framework.exceptions import ValidationError


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = '__all__'

    def create(self, validated_data):
        # Perform calculations
        instance = Candidate(**validated_data)
        print(validated_data)
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
            # print(f"belt_color: {candidate.belt_color}, age: {candidate.age}, weight: {candidate.weight}","Inside category")
        # if belt_color == 'Colour Belt' :
        #     if 5 <= age <= 9 :
        #         return 'Mini Sub Junior'
        #     elif 10 <= age <= 13 :
        #         return 'Sub Junior'
        #     elif 14 <= age <= 15 :
        #         return 'Cadet'
        #     elif 16 <= age <= 17 :
        #         return 'Junior'
        #     elif 18 <= age <= 21 :
        #         return 'Senior Below 21'
        #     else:
        #         return 'Senior Above 21'
        # elif belt_color == 'Black Belt':
        #     if age <= 12 :
        #         return 'Sub Junior'
        #     elif 13 <= age <= 15 :
        #         return 'Cadet'
        #     elif 15 <= age < 18 :
        #         return 'Junior'
        #     elif 18 <= age <= 21 :
        #         return 'Senior Below 21'
        #     else:
        #         return 'Senior Above 21'
        # print(f"Invalid combination: belt_color={belt_color}, age={age}, weight={weight}")
        # return None

    def calculate_weight_category(self, candidate):
        # weight_categories = {
        #     'Colour Belt': {
        #         'Mini Sub Junior': {
        #             (0, 20): 'Kumite -20 Kg',
        #             (21, 25): 'Kumite -25 Kg',
        #             (26, float('inf')): 'Kumite +25 Kg'
        #         },
        #         'Sub Junior': {
        #             (0, 30): 'Kumite -30 Kg',
        #             (31, 35): 'Kumite -35 Kg',
        #             (36, 40): 'Kumite -40 Kg',
        #             (41, 45): 'Kumite -45 Kg',
        #             (46, float('inf')): 'Kumite +45 Kg'
        #         },
        #         'Cadet': {
        #             (0, 45): 'Kumite -45 Kg',
        #             (46, 50): 'Kumite -50 Kg',
        #             (51, 55): 'Kumite -55 Kg',
        #             (56, 60): 'Kumite -60 Kg',
        #             (61, float('inf')): 'Kumite +60 Kg'
        #         },
        #         'Junior': {
        #             (0, 50): 'Kumite -50 Kg',
        #             (51, 55): 'Kumite -55 Kg',
        #             (56, 60): 'Kumite -60 Kg',
        #             (61, 65): 'Kumite -65 Kg',
        #             (66, float('inf')): 'Kumite +65 Kg'
        #         }
        #     },
        #     'Black Belt': {
        #         'Sub Junior': {
        #             (0, 30): 'Kumite -30 Kg',
        #             (31, 35): 'Kumite -35 Kg',
        #             (36, 40): 'Kumite -40 Kg',
        #             (41, 45): 'Kumite -45 Kg',
        #             (46, float('inf')): 'Kumite +45 Kg'
        #         },
        #         'Cadet': {
        #             (0, 45): 'Kumite -45 Kg',
        #             (46, 50): 'Kumite -50 Kg',
        #             (51, 55): 'Kumite -55 Kg',
        #             (56, 60): 'Kumite -60 Kg',
        #             (61, 65): 'Kumite -65 Kg',
        #             (66, float('inf')): 'Kumite +65 Kg'
        #         },
        #         'Junior': {
        #             (0, 50): 'Kumite -50 Kg',
        #             (51, 55): 'Kumite -55 Kg',
        #             (56, 60): 'Kumite -60 Kg',
        #             (61, 65): 'Kumite -65 Kg',
        #             (66, float('inf')): 'Kumite +65 Kg'
        #         }
        #     }
        # }

        # belt_color = candidate.belt_color
        # category = candidate.category
        # weight = candidate.weight
        # if belt_color in weight_categories:
        #     if category in weight_categories[belt_color]:
        #         for weight_range, kumite_category in weight_categories[belt_color][category].items():
        #             if weight_range[0] <= weight <= weight_range[1]:
        #                 return kumite_category
        #         return ValidationError(f'No kumite category found for weight: {weight}')
        #     else:
        #         return ValidationError(f'No kumite category found for category: {category}')
        # else:
        #     return ValidationError(f'No kumite category found for belt color: {belt_color}')
        
        if candidate.category and candidate.kumite:
            print(f"belt_color: {candidate.belt_color}, age: {candidate.age}, weight: {candidate.weight}","inside weight category")

            if candidate.belt_color == 'Colour Belt':
                if candidate.category == 'Mini Sub Junior':
                    if candidate.weight <= 20:
                        return 'Kumite -20 Kg'
                    elif 21 <= candidate.weight <= 25:
                        return 'Kumite -25 Kg'
                    else:
                        return 'Kumite +25 Kg'
                elif candidate.category=='Sub Junior':
                    if candidate.weight<=30:
                        return 'Kumite -30 Kg'
                    elif 30<candidate.weight<=35:
                        return 'Kumite -35 Kg'
                    elif 36<=candidate.weight<=40:
                        return 'Kumite -40 Kg'
                    elif 41<=candidate.weight<=45:
                        return 'Kumite -45 Kg'
                    else:
                        return 'Kumite +45 Kg'
                elif candidate.category=='Cadet':
                    if candidate.weight<=45:
                        return 'Kumite -45 Kg'
                    elif 46<=candidate.weight<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=candidate.weight<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=candidate.weight<=60:
                        return 'Kumite -60 Kg'
                    else:
                        return 'Kumite +60 Kg'
                elif candidate.category=='Junior':
                    if candidate.weight<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=candidate.weight<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=candidate.weight<=60:
                        return 'Kumite -60 Kg'
                    elif 61<=candidate.weight<=65:
                        return 'Kumite -65 Kg'
                    else:
                        return 'Kumite +65 Kg'
                else:
                    if candidate.weight<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=candidate.weight<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=candidate.weight<=60:
                        return 'Kumite -60 Kg'
                    elif 61<=candidate.weight<=65:
                        return 'Kumite -65 Kg'
                    elif 66<=candidate.weight<=70:
                        return 'Kumite -70 Kg'
                    elif 71<=candidate.weight<=75:
                        return 'Kumite -75 Kg'
                    else:
                        return 'Kumite +75 Kg'
            else:
                if candidate.category=='Sub Junior':
                    if candidate.weight<=30:
                        return 'Kumite -30 Kg'
                    elif 31<=candidate.weight<=35:
                        return 'Kumite -35 Kg'
                    elif 36<=candidate.weight<=40:
                        return 'Kumite -40 Kg'
                    elif 41<=candidate.weight<=45:
                        return 'Kumite -45 Kg'
                    else:
                        return 'Kumite +45 Kg'
                elif candidate.category=='Cadet':
                    if candidate.weight<=45:
                        return 'Kumite -45 Kg'
                    elif 46<=candidate.weight<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=candidate.weight<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=candidate.weight<=60:
                        return 'Kumite -60 Kg'
                    elif 61<=candidate.weight<=65:
                        return 'Kumite -65 Kg'
                    else:
                        return 'Kumite +65 Kg'
                elif candidate.category=='Junior':
                    if candidate.weight<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=candidate.weight<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=candidate.weight<=60:
                        return 'Kumite -60 Kg'
                    elif 61<=candidate.weight<=65:
                        return 'Kumite -65 Kg'
                    else:
                        return 'Kumite +65 Kg'
                else:
                    if candidate.weight<=50:
                        return 'Kumite -50 Kg'
                    elif 51<=candidate.weight<=55:
                        return 'Kumite -55 Kg'
                    elif 56<=candidate.weight<=60:
                        return 'Kumite -60 Kg'
                    elif 61<=candidate.weight<=65:
                        return 'Kumite -65 Kg'
                    elif 66<=candidate.weight<=70:
                        return 'Kumite -70 Kg'
                    elif 71<=candidate.weight<=75:
                        return 'Kumite -75 Kg'
                    else:
                        return 'Kumite +75 Kg'
                    
        print(f"Invalid combination: belt_color={candidate.belt_color}, category={candidate.category}, kumite={candidate.kumite}")
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
        self.update_club_fees_on_entry_fee_change(instance, new_entry_fee, old_entry_fee)
        instance.weight = validated_data.get('weight', instance.weight)
        instance.belt_color = validated_data.get('belt_color', instance.belt_color)
        instance.age = validated_data.get('age', instance.age)
        instance.name = validated_data.get('name', instance.name)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.kumite = validated_data.get('kumite', instance.kumite)
        instance.kata = validated_data.get('kata', instance.kata)
        instance.colours=validated_data.get('colours',instance.colours)
        # Recalculate category and weight category
        instance.category = self.calculate_category(instance)
        instance.chest_no=self.assign_chest_no(instance)
        print(instance.category)
        instance.weight_category = self.calculate_weight_category(instance)
        print(instance.weight_category)

        # Update other fields in the instance

        instance.save()

        return instance
    

    def update_club_fees_on_entry_fee_change(self, candidate, new_entry_fee, old_entry_fee):
        # Calculate the difference in entry fees
        fee_difference = new_entry_fee - old_entry_fee
        print("entered update club fee",fee_difference)
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
                content = f'Dear {instance.coach_name},\n\nWe are pleased to inform you that your payment for the championship registration has been successfully received. Wishing you the utmost success in the upcoming championship.\n\nBest regards,\nOrganization committee,\nJapan Karate Do Kenyu Ryu India'
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