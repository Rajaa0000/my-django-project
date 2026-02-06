from django.urls import path
from . import views

urlpatterns = [
    path('getPersonalInfo',views.getPersonalInfo.as_view(),name="getPersonalInfo"),
    path("getPatients",views.getPatients.as_view(),name="getPatients"),
    path("getTodayPatients",views.getTodayPatients.as_view(),name="getTodayPatients"),
    path("getServices",views.getServices.as_view(),name="getServices"),
    path("CreateMessageDoc",views.CreateMessageDoc.as_view(),name="CreateMessageDoc"),
    path('getPatientInfo/<int:patient_id>', views.getPatientInfo.as_view(),name="getPatientInfo"),
    path("checkAppointment/<int:appointment_id>/<str:action>",views.checkAppointment.as_view(),name="checkAppointment")
    
]