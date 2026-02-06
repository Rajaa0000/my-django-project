from django.db import models
from django.contrib.auth.models import AbstractUser

# ==========================================
# 1. CUSTOM USER MODEL
# ==========================================
class User(AbstractUser):
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('admin', 'Admin'),
    ]
    
    # Field to store the ID from the specific role table
    user_role_id = models.IntegerField(null=True, blank=True)
    user_role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.user_role})"

# ==========================================
# 2. ROLE TABLES (CLEANED)
# ==========================================

class Speciality(models.Model):
    speciality_id = models.AutoField(primary_key=True)
    speciality_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'speciality'

class Doctor(models.Model):
    doctor_id = models.AutoField(primary_key=True)
    # Removed: pwd, firstname, lastname, email (Now in User model)
    doctor_phone = models.IntegerField()
    doctor_address = models.CharField(max_length=200)
    doctor_willaya = models.CharField(max_length=50)
    doctor_pic = models.BinaryField(null=True, blank=True)
    doctor_cotas = models.IntegerField()
    doctor_speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE, db_column='doctor_speciality_id')
    doctor_leftcotas = models.IntegerField()

    class Meta:
        db_table = 'doctor'

class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True)
    # Removed: pwd, firstname, lastname, mail (Now in User model)
    patient_companyid = models.IntegerField()
    patient_datebirth = models.DateField()
    patient_cancer = models.BooleanField(default=False)
    patient_leftcotas = models.IntegerField()
    patient_address = models.CharField(max_length=200)
    patient_phone = models.IntegerField()
    patient_pic = models.BinaryField()
    patient_willaya = models.CharField(max_length=50)

    class Meta:
        db_table = 'patient'

class Leader(models.Model):  # Renamed from Admin
    admin_id = models.AutoField(primary_key=True)
    # Removed: admin_pwd, admin_email (Now in User model)
    admin_willaya = models.CharField(max_length=50)
    admin_status = models.BooleanField(default=False)

    class Meta:
        db_table = 'leader'

# ==========================================
# 3. REMAINING TABLES (NO CHANGES)
# ==========================================

class Service(models.Model):
    service_id = models.AutoField(primary_key=True)
    service_name = models.CharField(max_length=100)
    service_duration = models.TimeField()
    service_price = models.IntegerField()
    service_description = models.CharField(max_length=500)
    doc = models.ForeignKey(Doctor, on_delete=models.CASCADE, db_column='doc_id')

    class Meta:
        db_table = 'service'

class Appointment(models.Model):
    apointment_id = models.AutoField(primary_key=True)
    apointment_doc = models.ForeignKey(Doctor, on_delete=models.CASCADE, db_column='apointment_doc')
    apointment_service = models.ForeignKey(Service, on_delete=models.CASCADE, db_column='apointment_service')
    apointment_pat = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='apointment_pat')
    apointment_date = models.DateTimeField()
    apointment_urgent = models.BooleanField(default=False)
    apointment_status = models.BooleanField(default=False)
    apointment_comment = models.CharField(max_length=1000)

    class Meta:
        db_table = 'apointment'

class Ordonance(models.Model):
    ordonance_id = models.AutoField(primary_key=True)
    ordonance_apointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, db_column='ordonance_apointment')
    ordonance_file = models.BinaryField()
    ordonance_description = models.CharField(max_length=500)

    class Meta:
        db_table = 'ordonance'

class MessageDoc(models.Model):
    message_id = models.AutoField(primary_key=True)
    message_title = models.CharField(max_length=100)
    message_urgent = models.BooleanField(default=False)
    message_text = models.CharField(max_length=1000)
    message_sender = models.ForeignKey(Doctor, on_delete=models.CASCADE, db_column='message_sender')
    message_status = models.BooleanField(default=False)
    message_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messagedoc'

class MessagePat(models.Model):
    message_id = models.AutoField(primary_key=True)
    message_title = models.CharField(max_length=100)
    message_urgent = models.BooleanField(default=False)
    message_text = models.CharField(max_length=1000)
    message_sender = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='message_sender')
    message_status = models.BooleanField(default=False)
    message_date = models.DateTimeField(auto_now_add=True)
    message_pic = models.BinaryField(null=True, blank=True)

    class Meta:
        db_table = 'messagpat'