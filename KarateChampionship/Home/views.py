from .models import Club, Candidate
from .serializers import ClubSerializer, CandidateSerializer, ClubStatisticsSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .utilities import genarate_otp
from datetime import datetime
from django.db.models import Sum, Count,Q
from django.shortcuts import get_object_or_404
from rest_framework.parsers import FormParser


class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer
    permission_classes = [AllowAny]


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        club = serializer.save()  # Save the user instance
        refresh = RefreshToken.for_user(club)
        # otp = genarate_otp(club)

        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': ClubSerializer(club).data,
        }
        return Response(data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['POST'])        
    def login(self, request):
        email = request.data.get('email')
        password=request.data.get('password')
        if email :
            try:
                club=Club.objects.get(email=email)
                if not club.is_active:
                            return Response({"message": "Your account has been deactivated by admin"},status=status.HTTP_403_FORBIDDEN)
                if club.check_password(password):
                    refresh = RefreshToken.for_user(club)
                    data = {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'user': ClubSerializer(club).data,
                        }
                    return Response(data, status=status.HTTP_200_OK)
            except:
                    return Response({"message":"Invalid Credentials"},status=status.HTTP_401_UNAUTHORIZED)
            
    @action(detail=False, methods=['POST'])     
    def otpcreate(self,request):
         email=request.data.get('email')
         try:
            club=Club.objects.get(email=email)
            return Response({"error":"Active Club found in gven Email Id"},status=status.HTTP_401_UNAUTHORIZED)
         except:
            otp=genarate_otp(email)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data={
                "otp":otp,
                "time": current_time,
            }
            return Response(data,status=status.HTTP_200_OK)
         
    @action(detail=False, methods=['GET'])
    def club_statistics(self, request, pk=None):
        club = get_object_or_404(Club, pk=pk)
        
        club_data = Club.objects.filter(pk=pk).annotate(
            total_candidates=Count('candidate'),
            total_kata_candidates=Count('candidate', filter=Q(candidate__kata=True, candidate__kumite=False)),
            total_kumite_candidates=Count('candidate', filter=Q(candidate__kumite=True,  candidate__kata=False)),
            total_kumite_and_kata_candidates=Count('candidate', filter=Q(candidate__kumite=True,  candidate__kata=True)),

            total_entry_fee=Sum('candidate__entry_fee'),
            total_kata_entry_fee=Sum('candidate__entry_fee', filter=Q(candidate__kata=True, candidate__kumite=False)),
            total_kumite_entry_fee=Sum('candidate__entry_fee', filter=Q(candidate__kumite=True, candidate__kata=False)),
            total_both_entry_fee=Sum('candidate__entry_fee', filter=Q(candidate__kata=True, candidate__kumite=True)),
        )

        serializer = ClubStatisticsSerializer(club_data, many=True)

        # Extracting data for the first club (assuming only one club will be in the result)
        club_stats = serializer.data[0]

        # Reformatting the data
        result_data = {
            "Email": club_stats["email"],
            "Phone": club_stats["phone"],
            "Total_candidates": club_stats["total_candidates"],
            "Kata_only_candidates_count": club_stats["total_kata_candidates"],
            "Kumite_only_candidates_count": club_stats["total_kumite_candidates"],
            "Kumite_and_Kata_candidates_count": club_stats["total_kumite_and_kata_candidates"],
            "Total_kata_only_entry_fee": club_stats["total_kata_entry_fee"],
            "Total_kumite_only_entry_fee": club_stats["total_kumite_entry_fee"],
            "Total_Kata & Kumite entry_fee": club_stats["total_both_entry_fee"],
            "Total_club_entry_fee": club_stats["total_entry_fee"],
        }

        return Response(result_data, status=status.HTTP_200_OK)
    


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    permission_classes = [AllowAny]

    

    @action(detail=False, methods=['GET'])
    def filters(self, request):
        queryset = Candidate.objects.fliter()
        
        filters = {
            'gender': self.request.query_params.get('gender', None),
            'belt_color': self.request.query_params.get('belt_color', None),
            'kata': self.request.query_params.get('kata', None),
            'kumite': self.request.query_params.get('kumite', None),
            'category': self.request.query_params.get('category', None),
            'weight_category': self.request.query_params.get('weight_category', None),
        }

        for key, value in filters.items():
            if value is not None:
                queryset = queryset.filter(**{key: value})

        return Response(queryset.values(), status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['GET'])
    def club_candidates(self, request):
        try:
            club= self.request.query_params.get('club', None)
            candidates=Candidate.objects.filter(club=club)
            serializer = self.get_serializer(candidates,many=True)
        except:
            pass
        return Response(serializer.data, status=status.HTTP_200_OK)

    # @action(detail=False, methods=['POST'], parser_classes=[FormParser])
    # def filtered_candidates(self, request):
    #     # Get filter parameters from the form data
    #     print("ooooooooooooooooooooooooooooooooo")
    #     category = request.data.get('category')
    #     weight_category = request.data.get('weight_category')
    #     gender = request.data.get('gender')
    #     belt_color = request.data.get('belt_color')
    #     kata = request.data.get('kata')
    #     kumite = request.data.get('kumite')

    #     # Query candidates based on filter parameters
    #     candidates = Candidate.objects.filter(
    #         category=category,
    #         weight_category=weight_category,
    #         gender=gender,
    #         belt_color=belt_color,
    #         kata=kata,
    #         kumite=kumite
    #     ).order_by('age', 'weight')

    #     # Serialize the candidates
    #     serializer = CandidateSerializer(candidates, many=True)

    #     # Return the serialized data
    #     return Response(serializer.data, status=status.HTTP_200_OK)


# class OtpHandler(APIView):
#     def post(self,request):
#          email=request.data.get('email')
#          try:
#             club=Club.objects.get(email=email)
#             return Response({"error":"Active Club found in gven Email Id"},status=status.HTTP_401_UNAUTHORIZED)
#          except:
#             otp=genarate_otp(email)
#             current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#             data={
#                 "otp":otp,
#                 "time": current_time,
#             }
#             return Response(data,status=status.HTTP_200_OK)













# class UserViewSet(viewsets.ModelViewSet):
#     queryset = Club.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = [AllowAny]

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()

#         return Response(self.get_serializer(user).data, status=status.HTTP_201_CREATED)
        # if request.user._is_superuser:
            # queryset=Order.objects.filter(status='pending')
        # else:
        # order=Order.objects.get(order_id=order_id)
        # order.current_position=request.user.staff.hub
        # order.save() 
        # # queryset=Order.objects.filter(booking__from_hub=request.user.staff.hub,status='pending')
        # return OrderSerializer(order).data
# class CandidateViewSet(viewsets.ModelViewSet):
#     queryset = Candidate.objects.all()
#     serializer_class = CandidateSerializer


# class ClubRegistrationView(CreateAPIView):
#     serializer_class = ClubSerializer
#     permission_classes = [AllowAny]
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         club = serializer.save()  # Save the user instance
#         # Generate token
#         refresh = RefreshToken.for_user(club)

#         data = {
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#         }
#         return Response(data, status=status.HTTP_200_OK)