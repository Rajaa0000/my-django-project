from django.urls import path
from . import views  # Ensure you have a views file

urlpatterns = [
    path("getDoctorMessages",views.getDoctorMessages.as_view(),name="getDoctorMessages"),
    path("getPatientMessages",views.getPatientMessages.as_view(),name="getPatientMessages"),
    path("getDoctorList",views.getDoctorList.as_view(),name="getDoctorList"),
    path("getPatientList",views.getPatientList.as_view(),name="getPatientList"),
    path("getInterface",views.getInterface.as_view(),name="getInterface"),
    path("CreatePatient",views. CreatePatient.as_view(),name="CreatePatient"),
   path('user-manage/<int:id>',views.UserDetailView.as_view(), name='user-detail-manage'),
   path("markAsDone/<int:message_id>/<str:message_type>",views.markAsDone.as_view(),name="markAsDone"),
   


]