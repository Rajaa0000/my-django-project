from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated # Import this!
from sharedapp.serializers import PatientSerializer,UserSerializer,AppointmentSerializer,OrdonanceSerializer,MessagePatSerializer,ServiceSerializer,DoctorWithUserSerializer,SpecialitySerializer
from sharedapp.models import Patient,User,Appointment,Ordonance,Doctor,MessagePat,Speciality,Service
from rest_framework import generics
from django.db import transaction
from django.utils import timezone


# 1. Get all Specialities
class SpecialityListView(generics.ListAPIView):
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer

# 2. Get Doctors by Speciality (Including User data)
class DoctorsBySpecialityView(APIView):
    def get(self, request, spec_id):
        # Fetch doctors in this speciality
        doctors = Doctor.objects.filter(doctor_speciality_id=spec_id)
        
        results = []
        for doc in doctors:
            # Find the corresponding User record
            user_account = User.objects.filter(user_role='doctor', user_role_id=doc.doctor_id).first()
            
            # Merge data
            doc_data = DoctorWithUserSerializer(doc).data
            if user_account:
                doc_data['username'] = user_account.username
                doc_data['first_name'] = user_account.first_name
                doc_data['last_name'] = user_account.last_name
                doc_data['email'] = user_account.email
            
            results.append(doc_data)
            
        return Response(results, status=status.HTTP_200_OK)

# 3. Get Services for a specific Doctor
class DoctorServicesView(generics.ListAPIView):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        doctor_id = self.kwargs['doctor_id']
        return Service.objects.filter(doc_id=doctor_id)


class ManageAppointment(APIView):
    # Ensure only logged-in users can access this
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        """ CREATE APPOINTMENT """
        # We use .copy() because request.data is immutable (can't be changed) by default
        data = request.data.copy()
        
        try:
            # Step 1: Securely get the patient ID from the logged-in User profile
            patient_id = request.user.user_role_id
            if not patient_id or request.user.user_role != 'patient':
                return Response({"error": "Only patients can create appointments."}, status=403)

            # Step 2: Lock the rows for Quota calculation (Prevents race conditions)
            doctor = Doctor.objects.select_for_update().get(doctor_id=data.get('apointment_doc'))
            patient = Patient.objects.select_for_update().get(patient_id=patient_id)
            
            # Step 3: Quota Validation Logic
            if doctor.doctor_leftcotas <= 0:
                return Response({"error": "Doctor has no quotas left."}, status=400)
            
            if not patient.patient_cancer and patient.patient_leftcotas <= 0:
                return Response({"error": "Patient has no quotas left."}, status=400)

            # Step 4: Inject IDs into data for Serializer validation
            data['apointment_pat'] = patient_id
            
            serializer = AppointmentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                
                # Step 5: Update Quotas in Database
                doctor.doctor_leftcotas -= 1
                doctor.save()
                
                if not patient.patient_cancer:
                    patient.patient_leftcotas -= 1
                    patient.save()
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except (Doctor.DoesNotExist, Patient.DoesNotExist):
            return Response({"error": "Doctor or Patient profile not found."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @transaction.atomic
    def put(self, request, pk):
        """ MODIFY APPOINTMENT (Delete if logic fails) """
        try:
            # We get the existing appointment using the Primary Key from the URL
            old_appointment = Appointment.objects.get(apointment_id=pk)
            
            # 1. 'Undo' old quotas first to see if modification is possible
            doc_old = old_appointment.apointment_doc
            pat_old = old_appointment.apointment_pat
            
            doc_old.doctor_leftcotas += 1
            doc_old.save()
            if not pat_old.patient_cancer:
                pat_old.patient_leftcotas += 1
                pat_old.save()

            # 2. Try to apply new data
            data = request.data.copy()
            data['apointment_pat'] = request.user.user_role_id # Security check again
            
            serializer = AppointmentSerializer(old_appointment, data=data)
            
            if serializer.is_valid():
                new_doc = Doctor.objects.select_for_update().get(doctor_id=data.get('apointment_doc'))
                new_pat = Patient.objects.select_for_update().get(patient_id=data.get('apointment_pat'))
                
                # Check if new quotas are available
                if new_doc.doctor_leftcotas > 0 and (new_pat.patient_cancer or new_pat.patient_leftcotas > 0):
                    serializer.save()
                    new_doc.doctor_leftcotas -= 1
                    new_doc.save()
                    if not new_pat.patient_cancer:
                        new_pat.patient_leftcotas -= 1
                        new_pat.save()
                    return Response(serializer.data)

            # 3. If validation fails or quotas are full, DELETE the original (per your instructions)
            old_appointment.delete()
            return Response({"message": "Modification failed. Appointment has been deleted."}, status=400)

        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found."}, status=404)

    @transaction.atomic
    def delete(self, request, pk):
        """ CANCEL APPOINTMENT """
        try:
            appointment = Appointment.objects.get(apointment_id=pk)
            
            # Security: Ensure only the owner (patient) can delete their own appointment
            if appointment.apointment_pat_id != request.user.user_role_id:
                return Response({"error": "You cannot cancel someone else's appointment."}, status=403)

            doctor = appointment.apointment_doc
            patient = appointment.apointment_pat

            # Return the quotas
            doctor.doctor_leftcotas += 1
            doctor.save()
            
            if not patient.patient_cancer:
                patient.patient_leftcotas += 1
                patient.save()

            appointment.delete()
            return Response({"message": "Appointment cancelled and quotas returned."}, status=status.HTTP_204_NO_CONTENT)

        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found."}, status=404)

class CreateMessagePat(generics.CreateAPIView):
    queryset = MessagePat.objects.all()
    serializer_class = MessagePatSerializer

    def perform_create(self, serializer):
        # 1. Find the Doctor instance using the ID from the User model
        # Note: Your model expects a Doctor instance, not just an integer
        patient_instance = Patient.objects.get(patient_id=self.request.user.user_role_id)
        
        # 2. Save the message with the sender
        # 'message_date' is auto-generated because of auto_now_add=True in your model
        serializer.save(message_sender=patient_instance)


class getPersonalInfo(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            # 1. Use the ID stored on the User model to find the Doctor
            # We use user_role_id because that's your custom link
            patient =Patient.objects.get(patient_id=request.user.user_role_id)
            the_user = User.objects.get(id=request.user.id)
            # 2. Pass the 'doctor' object to the serializer
            serializer1 = PatientSerializer(patient)
            serializer2 = UserSerializer(the_user)
            combined_data = {
            "profile1": serializer1.data,
            "profile2":serializer2.data,
            
            # "appointments": appt_serializer.data  <-- You can add this too!
        }
            # 3. Return the serialized data
            return Response(combined_data, status=status.HTTP_200_OK)
            
        except Patient.DoesNotExist:
            return Response(
                {"error": "Patient profile not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
class getOrdonance(APIView):
    permission_classes = [IsAuthenticated]
   
    def get(self, request):
        try:
            # 1. Get all appointments for this patient
            appointments = Appointment.objects.filter(apointment_pat_id=request.user.user_role_id)
            
            response_list = []
            for item in appointments: 
                # 2. Get the QuerySet (List) of ordonances for this specific appointment
                ordonances_queryset = Ordonance.objects.filter(ordonance_apointment_id=item.apointment_id)
                
                # 3. Only add to response if there is at least one ordonance
                if ordonances_queryset.exists():
                    # Find the doctor's User account
                    doctor_user = User.objects.filter(
                        user_role_id=item.apointment_doc_id, 
                        user_role='doctor'
                    ).first()

                    response_list.append({
                        # FIX: Added 'many=True' because ordonances_queryset is a list
                        "ordonanceInfo": OrdonanceSerializer(ordonances_queryset, many=True).data,
                        "doctorInfo": doctor_user.username if doctor_user else "Unknown Doctor",
                        "appointment_date": item.apointment_date
                    })
     
            return Response(response_list, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class getHistory(APIView):
    permission_classes = [IsAuthenticated]
   
    def get(self, request):
        try:
            # 1. Get all appointments for this patient
            appointments = Appointment.objects.filter(apointment_pat_id=request.user.user_role_id,
                                                      apointment_status=True)[:4]
     
            return Response(AppointmentSerializer(appointments,many=True).data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class getAppointments(APIView):
    permission_classes = [IsAuthenticated]
   
    def get(self, request):
        try:
            # Get the last 4 pending appointments
            appointments = Appointment.objects.filter(
                apointment_pat_id=request.user.user_role_id,
                apointment_status=False
            )[:4]

            responseList = []
            for item in appointments:
                # 1. Use _id to get the number. 
                # This prevents Django from doing an extra database query for the Doctor object here.
                doc_id_number = item.apointment_doc_id 

                # 2. Get the Doctor profile (for the address)
                doctor_profile = Doctor.objects.get(doctor_id=doc_id_number)

                # 3. Get the User account (for the username)
                # Use the doc_id_number we extracted above
                user_account = User.objects.filter(
                    user_role_id=doc_id_number, 
                    user_role='doctor'
                ).first()

                responseList.append({
                    "appointment": AppointmentSerializer(item).data,
                    "doctor_name": user_account.username if user_account else "Unknown",
                    "doctor_address": doctor_profile.doctor_address
                })
                
            return Response(responseList, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)