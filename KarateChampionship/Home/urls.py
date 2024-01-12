from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'clubs', ClubViewSet)
router.register(r'candidates', CandidateViewSet)
# router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # path('otp/',OtpHandler.as_view()),
    path('clubs/<int:pk>/statistics/', ClubViewSet.as_view({'get': 'club_statistics'}), name='club-statistics'),
    path('candidates/filtered/', CandidateViewSet.as_view({'post': 'filtered_candidates'}), name='filtered-candidates'),

]
