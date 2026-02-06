from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    User, Speciality, Doctor, Patient, Leader, 
    Service, Appointment, Ordonance, MessageDoc, MessagePat
)



class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Exclude password so it can't be modified here
        fields = ['id', 'username', 'email', 'user_role', 'user_role_id', 'first_name', 'last_name']
        read_only_fields = ['id']
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_role', 'user_role_id']

class SpecialitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = '__all__'

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        # We explicitly exclude the BinaryField to prevent errors
        exclude = ['doctor_pic']

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        # We explicitly exclude the BinaryField here too
        exclude = ['patient_pic']

class LeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leader
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

class OrdonanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ordonance
        exclude = ['ordonance_file']
        

class MessageDocSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageDoc
        fields = '__all__'
        read_only_fields = ["message_sender", "message_date","message_status"]

class MessagePatSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessagePat
        exclude = ["message_pic"]
        read_only_fields = ["message_sender", "message_date","message_status"]



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    # We define the extra fields the frontend must send
    user_role = serializers.CharField(write_only=True)
    role_specific_id = serializers.IntegerField(write_only=True)

    def validate(self, attrs):
        role = attrs.get("user_role")
        role_id = attrs.get("role_specific_id")
        password = attrs.get("password")

        # 1. Verification Step: Check if the ID exists in the specific table
        exists = False
        if role == 'doctor':
            exists = Doctor.objects.filter(doctor_id=role_id).exists()
        elif role == 'patient':
            exists = Patient.objects.filter(patient_id=role_id).exists()
        elif role == 'admin':
            exists = Leader.objects.filter(admin_id=role_id).exists()

        if not exists:
            raise serializers.ValidationError(f"Invalid ID: No {role} found with ID {role_id}")

        # 2. Find the linked User account
        # We find the User where user_role and user_role_id match the inputs
        try:
            user = User.objects.get(user_role=role, user_role_id=role_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user account linked to this role and ID.")

        # 3. Check password
        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password.")

        # 4. Generate Tokens
        refresh = self.get_token(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_role': user.user_role,
            'user_role_id': user.user_role_id,
            'username': user.username
        }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to the encrypted token payload
        token['user_role'] = user.user_role
        token['user_role_id'] = user.user_role_id
        return token
    
    
class DoctorWithUserSerializer(serializers.ModelSerializer):
    # We add custom fields to hold the User data
    username = serializers.CharField(source='user_link.username', read_only=True)
    first_name = serializers.CharField(source='user_link.first_name', read_only=True)
    last_name = serializers.CharField(source='user_link.last_name', read_only=True)
    email = serializers.CharField(source='user_link.email', read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'doctor_id', 'doctor_phone', 'doctor_address', 'doctor_willaya', 
            'doctor_cotas', 'doctor_leftcotas', 'doctor_speciality',
            'username', 'first_name', 'last_name', 'email'
        ]