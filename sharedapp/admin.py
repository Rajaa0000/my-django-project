from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Speciality, Doctor, Patient, Leader, Service, Appointment, Ordonance, MessageDoc, MessagePat

# ==========================================
# 1. CUSTOM USER ADMIN
# ==========================================
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Add your custom fields to the fieldsets so they show up in the edit page
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('user_role', 'user_role_id')}),
    )
    # Add your custom fields to the creation page
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('user_role', 'user_role_id')}),
    )
    list_display = ('username', 'email', 'user_role', 'user_role_id', 'is_staff')
    list_filter = ('user_role', 'is_staff', 'is_superuser')

# ==========================================
# 2. ROLE TABLE ADMINS
# ==========================================

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('doctor_id', 'doctor_willaya', 'doctor_phone', 'doctor_speciality')
    search_fields = ('doctor_willaya', 'doctor_phone')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'patient_companyid', 'patient_willaya', 'patient_phone')
    list_filter = ('patient_cancer', 'patient_willaya')

@admin.register(Leader)
class LeaderAdmin(admin.ModelAdmin):
    list_display = ('admin_id', 'admin_willaya', 'admin_status')

# ==========================================
# 3. OTHER TABLES
# ==========================================

@admin.register(Speciality)
class SpecialityAdmin(admin.ModelAdmin):
    list_display = ('speciality_id', 'speciality_name')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'service_price', 'doc')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('apointment_id', 'apointment_doc', 'apointment_pat', 'apointment_date', 'apointment_status')
    list_filter = ('apointment_status', 'apointment_urgent', 'apointment_date')

@admin.register(Ordonance)
class OrdonanceAdmin(admin.ModelAdmin):
    list_display = ('ordonance_id', 'ordonance_apointment')

admin.site.register(MessageDoc)
admin.site.register(MessagePat)