from django.urls import path
from .views import MyTokenObtainPairView

urlpatterns = [
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
]