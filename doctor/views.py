from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,AllowAny  # Import this!
from sharedapp.serializers import DoctorSerializer,UserSerializer,PatientSerializer,AppointmentSerializer,ServiceSerializer,MessageDocSerializer
from sharedapp.models import Doctor,User,Patient,Appointment,Service,MessageDoc
from django.utils import timezone
from rest_framework import generics
from django.db import transaction


class checkAppointment(APIView):
    def patch(self, request, appointment_id, action):
        """
        action: 'cancel' or 'complete'
        """
        try:
            with transaction.atomic():
                # 1. Get the appointment
                try:
                    appt = Appointment.objects.select_related('apointment_doc', 'apointment_pat').get(apointment_id=appointment_id)
                except Appointment.DoesNotExist:
                    return Response({"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)

                if action == "cancel":
                    # 2. Increase Quotas (Refund)
                    doctor = appt.apointment_doc
                    patient = appt.apointment_pat

                    doctor.doctor_leftcotas += 1
                    patient.patient_leftcotas += 1

                    doctor.save()
                    patient.save()

                    # 3. Delete the appointment record
                    appt.delete()

                    return Response({"message": "Appointment cancelled and quotas refunded."}, status=status.HTTP_200_OK)

                elif action == "complete":
                    # 4. Simply mark as done
                    appt.apointment_status = True
                    appt.save()
                    
                    return Response({"message": "Appointment marked as completed."}, status=status.HTTP_200_OK)

                else:
                    return Response({"error": "Invalid action. Use 'cancel' or 'complete'."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreateMessageDoc(generics.CreateAPIView):
    queryset = MessageDoc.objects.all()
    serializer_class = MessageDocSerializer

    def perform_create(self, serializer):
        # 1. Find the Doctor instance using the ID from the User model
        # Note: Your model expects a Doctor instance, not just an integer
        doctor_instance = Doctor.objects.get(doctor_id=self.request.user.user_role_id)
        
        # 2. Save the message with the sender
        # 'message_date' is auto-generated because of auto_now_add=True in your model
        serializer.save(message_sender=doctor_instance)





class getServices(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            
            services = Service.objects.filter(doc=request.user.user_role_id)
            return Response(ServiceSerializer(services,many=True).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class getPatientInfo(APIView):
    permission_classes = [IsAuthenticated]

    # ADD 'patient_id' HERE (after request)
    def get(self, request, patient_id): 
        try:
            # Now 'patient_id' is available to use in your queries
            patient = Patient.objects.get(patient_id=patient_id)
            user = User.objects.filter(user_role="patient", user_role_id=patient_id).first()
          
            obj = {
                "patient_info": PatientSerializer(patient).data,
                "user_info": UserSerializer(user).data if user else None
            }

            return Response(obj, status=status.HTTP_200_OK)
                        
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class getPersonalInfo(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            # 1. Use the ID stored on the User model to find the Doctor
            # We use user_role_id because that's your custom link
            doctor = Doctor.objects.get(doctor_id=request.user.user_role_id)
            the_user = User.objects.get(id=request.user.id)
            # 2. Pass the 'doctor' object to the serializer
            serializer1 = DoctorSerializer(doctor)
            serializer2 = UserSerializer(the_user)
            combined_data = {
            "profile1": serializer1.data,
            "profile2":serializer2.data,
            
            # "appointments": appt_serializer.data  <-- You can add this too!
        }
            # 3. Return the serialized data
            return Response(combined_data, status=status.HTTP_200_OK)
            
        except Doctor.DoesNotExist:
            return Response(
                {"error": "Doctor profile not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
class getTodayPatients(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            today = timezone.now().date()
            
            # 1. Filter using the ID from the logged-in User
            todays_appointments = Appointment.objects.filter(
                apointment_date__date=today,
                apointment_doc__doctor_id=request.user.user_role_id
            )

            responseList = []
            for item in todays_appointments:
                # 2. FIX: Access patient_id via dot notation
                # item.apointment_pat is the Patient object
                p_id = item.apointment_pat.patient_id

                # 3. Find the base User account
                the_user = User.objects.filter(user_role_id=p_id, user_role="patient").first()
                
                # 4. FIX: Get the Patient object (item.apointment_pat IS the patient object already!)
                # You don't need to query Patient.objects.get() again.
                patient = item.apointment_pat

                responseList.append({
                    "patient_info": PatientSerializer(patient).data,
                    "user_info": UserSerializer(the_user).data if the_user else None,
                    "appointment_info": AppointmentSerializer(item).data
                })

            return Response(responseList, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class getPatients(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            # 1. Use the ID stored on the User model to find the Doctor
            # We use user_role_id because that's your custom link
            doctor = Doctor.objects.get(doctor_id=request.user.user_role_id)
            patients=Patient.objects.filter(patient_willaya=doctor.doctor_willaya)

            responseList=[]
            for item in patients:
                obj={}
                the_user = User.objects.filter(user_role_id=item.patient_id,user_role="patient").first()
                forthismatch_appointment=Appointment.objects.filter(apointment_pat=item.patient_id,
                                    apointment_doc=request.user.user_role_id).order_by('-apointment_date').first()
                if forthismatch_appointment :
                    obj["status"]="regulare suivi"
                    obj['last_visit_date']=forthismatch_appointment.apointment_date
                else :
                    obj["status"]="new patient for you "
                    obj['last_visit_date']="null"
                obj["username"]=the_user.username
                obj["patient_info"]=PatientSerializer(item).data

                responseList.append(obj)

            return Response(responseList, status=status.HTTP_200_OK)
                        
        except Doctor.DoesNotExist:
            return Response(
                            {"error": "Doctor profile not found."}, 
                            status=status.HTTP_404_NOT_FOUND)