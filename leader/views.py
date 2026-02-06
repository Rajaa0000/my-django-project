from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics
from rest_framework.permissions import IsAuthenticated ,AllowAny
from sharedapp.serializers import MessageDocSerializer,MessagePatSerializer,UserSerializer,DoctorSerializer,UserUpdateSerializer,PatientSerializer,AppointmentSerializer
from sharedapp.models import MessageDoc,MessagePat,User,Leader,Doctor,Patient,Appointment,Service
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.hashers import make_password

# 1. IMPORT YOUR MODELS AND SERIALIZERS HERE
# from .models import [MODEL_NAME]
# from .serializers import [SERIALIZER_NAME]


class markAsDone(APIView):
    def patch(self, request, message_id, message_type):
        try:
            if message_type == "doctor":
                obj = MessageDoc.objects.get(message_id=message_id)
            elif message_type == "patient":
                obj = MessagePat.objects.get(message_id=message_id)
            else:
                return Response(
                    {"error": "Invalid message type. Use 'doctor' or 'patient'."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update and save
            obj.message_status = True
            obj.save()

            return Response(
                {"message": f"{message_type.capitalize()} message marked as done."}, 
                status=status.HTTP_200_OK
            )

        except (MessageDoc.DoesNotExist, MessagePat.DoesNotExist):
            return Response(
                {"error": f"Message with ID {message_id} not found in {message_type} table."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    # We use 'id' as the lookup field (e.g., /api/user/5/)
    lookup_field = 'id'

    def perform_update(self, serializer):
        # This ensures that even if a password is sent in the request,
        # it is ignored during the update process.
        serializer.save()

    def perform_destroy(self, instance):
        # Optional: You might want to delete the associated Role profile 
        # (Doctor/Patient) when the User is deleted.
        role = instance.user_role
        role_id = instance.user_role_id
        
        # Delete the linked profile first
        if role == 'patient':
            Patient.objects.filter(patient_id=role_id).delete()
        elif role == 'doctor':
            Doctor.objects.filter(doctor_id=role_id).delete()
            
        # Delete the User
        instance.delete()

class CreatePatient(APIView):
    # Depending on your app, this might be Admin-only or Public
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        # We wrap this in a transaction so if the Patient save fails, 
        # the User isn't created either (no "orphan" accounts).
        try:
            with transaction.atomic():
                # 1. Extract data from request
                username = request.data.get('username')
                email = request.data.get('email')
                phone = request.data.get('patient_phone')
                company_id = request.data.get('patient_companyid')

                # 2. Formula for Default Password
                # Example: "Pat@" + company_id (e.g., Pat@12345)
                default_password = f"Pat@{company_id}"

                # 3. Create the Patient Profile first to get the patient_id
                new_patient = Patient.objects.create(
                    patient_companyid=company_id,
                    patient_datebirth=request.data.get('patient_datebirth'),
                    patient_cancer=request.data.get('patient_cancer', False),
                    patient_leftcotas=request.data.get('patient_leftcotas', 0),
                    patient_address=request.data.get('patient_address'),
                    patient_phone=phone,
                    patient_willaya=request.data.get('patient_willaya'),
                    patient_pic=b''  # As you requested
                )

                # 4. Create the User and link it
                new_user = User.objects.create(
                    username=username,
                    email=email,
                    user_role='patient',
                    user_role_id=new_patient.patient_id,
                    password=make_password(default_password) # Hashed for security
                )

                return Response({
                    "message": "Patient created successfully",
                    "username": new_user.username,
                    "generated_password": default_password, # Return this so the admin can tell the patient
                    "patient_id": new_patient.patient_id
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class getDoctorMessages(APIView):
    # Change to IsAuthenticated so request.user is always a valid User
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # 1. Get the current Leader's Willaya
            # We do this once OUTSIDE the loop
            leader = Leader.objects.get(admin_id=request.user.user_role_id)
            leader_willaya = leader.admin_willaya

            # 2. Get all pending messages
            messages = MessageDoc.objects.filter(message_status=False)
            
            object_list = []
            
            for item in messages:
                # 3. Get the Doctor profile of the sender
                # Note: item.message_sender is the Doctor instance (from your model definition)
                doctor = item.message_sender 
                
                # 4. Check if the Doctor is in the same Willaya as the Leader
                if doctor.doctor_willaya == leader_willaya:
                    # Find the User account linked to this doctor to get their name/info
                    user_info = User.objects.filter(user_role="doctor", user_role_id=doctor.doctor_id).first()
                    
                    object_list.append({
                        "message_info": MessageDocSerializer(item).data,
                        "user_info": UserSerializer(user_info).data if user_info else None
                    })

            return Response(object_list, status=status.HTTP_200_OK)
            
        except Leader.DoesNotExist:
            return Response({"error": "You are not registered as a Leader."}, status=403)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class getPatientMessages(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            # 1. Get the current Leader's Willaya
            # We do this once OUTSIDE the loop
            leader = Leader.objects.get(admin_id=request.user.user_role_id)
            leader_willaya = leader.admin_willaya

            # 2. Get all pending messages
            messages = MessagePat.objects.filter(message_status=False)
            
            object_list = []
            
            for item in messages:
                # 3. Get the Doctor profile of the sender
                # Note: item.message_sender is the Doctor instance (from your model definition)
                patient = item.message_sender 
                
                # 4. Check if the Doctor is in the same Willaya as the Leader
                if patient.patient_willaya == leader_willaya:
                    # Find the User account linked to this doctor to get their name/info
                    user_info = User.objects.filter(user_role="patient", user_role_id=patient.patient_id).first()
                    
                    object_list.append({
                        "message_info": MessagePatSerializer(item).data,
                        "user_info": UserSerializer(user_info).data if user_info else None
                    })

            return Response(object_list, status=status.HTTP_200_OK)
            
        except Leader.DoesNotExist:
            return Response({"error": "You are not registered as a Leader."}, status=403)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
class getDoctorList(APIView):
    
    def get(self, request):
        try:
            # 1. Use .filter() instead of .get() to get an iterable list
            doctors = Doctor.objects.all()
            
            object_list = []
            for item in doctors:
                # 2. Access the sender. 
                # Assuming 'message_sender' is a ForeignKey to User
                user_info = User.objects.filter(user_role_id=item.doctor_id,user_role='doctor').first() 
                
                # 3. Serializers need .data to be turned into JSON
                # Also, use () for the dictionary, not {} which creates a set
                object_list.append({
                    "doctor_info": DoctorSerializer(item).data,
                    "user_info": UserSerializer(user_info).data if user_info else None
                })

            return Response(object_list, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
class getPatientList(APIView):

    
    def get(self, request):
        try:
            # 1. Use .filter() instead of .get() to get an iterable list
            patients = Patient.objects.all()
            
            object_list = []
            for item in patients:
                # 2. Access the sender. 
                # Assuming 'message_sender' is a ForeignKey to User
                user_info = User.objects.filter(user_role_id=item.patient_id,user_role='patient').first() 
                
                # 3. Serializers need .data to be turned into JSON
                # Also, use () for the dictionary, not {} which creates a set
                object_list.append({
                    "patient_info": PatientSerializer(item).data,
                    "user_info": UserSerializer(user_info).data if user_info else None
                })

            return Response(object_list, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
class getInterface(APIView):
    def get(self, request):
        try:
            # 1. Statistics Counters
            response_object = {
                "total_number_patients": Patient.objects.count(),
                "total_number_doctors": Doctor.objects.count(),
                "total_number_appointments": Appointment.objects.count(),
                "total_number_doctmessages": MessageDoc.objects.count(),
                "total_number_pattmessages": MessagePat.objects.count(),
            }

            # 2. Get Today's Appointments
            today = timezone.now().date()
            # Note: filter using apointment_date__date
            todays_appointments = Appointment.objects.filter(apointment_date__date=today)

            object_list = []
            for item in todays_appointments:
                # IMPORTANT: Use .apointment_pat_id and .apointment_doc_id 
                # to get the integer ID from the ForeignKey
                patient_user = User.objects.filter(
                    user_role_id=item.apointment_pat_id, 
                    user_role='patient'
                ).first() 
                
                doctor_user = User.objects.filter(
                    user_role_id=item.apointment_doc_id, 
                    user_role='doctor'
                ).first() 
                
                # Fetch the service name using the ForeignKey ID
                service = Service.objects.filter(service_id=item.apointment_service_id).first()
                
                object_list.append({
                    "patient_name": patient_user.username if patient_user else "Unknown Patient",
                    "doctor_name": doctor_user.username if doctor_user else "Unknown Doctor",
                    "appointments_date": item.apointment_date,
                    "appointments_type": service.service_name if service else "N/A",
                    "appointments_status": item.apointment_status,
                })

            response_object["table_info"] = object_list
            return Response(response_object, status=status.HTTP_200_OK)
            
        except Exception as e:
            # This will now print the error to your console so you can see it!
            print(f"CRASH ERROR: {str(e)}")
            return Response(
                {"error": f"Internal Error: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )