from django.urls import path
from . import views  # Ensure you have a views file


urlpatterns = [
    path("getPersonalInfo",views.getPersonalInfo.as_view(),name="getPersonalInfo"),
    path("getOrdonance",views.getOrdonance.as_view(),name="getOrdonance"),
    path("getHistory",views.getHistory.as_view(),name="getHistory"),
    path("getAppointments",views.getAppointments.as_view(),name="getAppointments"),
    path("CreateMessagePat",views.CreateMessagePat.as_view(),name="CreateMessagePat"),
    path("ManageAppointment",views.ManageAppointment.as_view(),name="ManageAppointment"),
    
# Get all specialities: /api/specialities/
    path('specialities/', views.SpecialityListView.as_view(), name='speciality-list'),

    # Get doctors in speciality #5: /api/speciality/5/doctors/
    path('speciality/<int:spec_id>/doctors/', views.DoctorsBySpecialityView.as_view(), name='doctors-by-spec'),

    # Get services for doctor #10: /api/doctor/10/services/
    path('doct/<int:doctor_id>/services/', views.DoctorServicesView.as_view(), name='doct-services'),
]