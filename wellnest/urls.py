from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


urlpatterns = [
    path('admin/', admin.site.urls),
    path('sharedapp/',include('sharedapp.urls')),
    path('leader/',include('leader.urls')),
    path('doctor/',include('doctor.urls')),
    path('patient/',include('patient.urls')),

    
]