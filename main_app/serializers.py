from rest_framework import serializers
from .models import Doctor, Clinic, Patient, Specialty, Visit, DoctorAffiliation, Appointment, AppointmentStatusChoices
from django.db.models import Count
from django.utils import timezone

class DoctorAffiliationSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source='doctor.id', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    doctor_specialties = serializers.SerializerMethodField() 

    class Meta:
        model = DoctorAffiliation
        fields = ['doctor_id', 'doctor_name', 'doctor_specialties', 'office_address', 'working_schedule']

    def get_doctor_specialties(self, obj):
        return [specialty.name for specialty in obj.doctor.specialties.all()]

class ClinicSerializer(serializers.ModelSerializer):
    affiliations = DoctorAffiliationSerializer(many=True, read_only=True)
    affiliated_doctors_count = serializers.IntegerField(source='affiliations.count', read_only=True)
    affiliated_patients_count = serializers.SerializerMethodField()

    class Meta:
        model = Clinic
        fields = ['id', 'name', 'phone_number', 'city', 'state', 'address', 'email', 
                  'affiliated_doctors_count', 'affiliated_patients_count', 'affiliations']

    def get_affiliated_patients_count(self, obj):
        appointment_patient_ids = Appointment.objects.filter(clinic=obj).values_list('patient_id', flat=True)
        visit_patient_ids = Visit.objects.filter(clinic=obj).values_list('patient_id', flat=True)
        total_patient_ids = set(list(appointment_patient_ids) + list(visit_patient_ids))
        return len(total_patient_ids)

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name']

class DoctorSerializer(serializers.ModelSerializer):
    affiliated_clinics = serializers.IntegerField(source='affiliations.count', read_only=True)
    affiliated_patients = serializers.SerializerMethodField()
    specialties = SpecialtySerializer(many=True, read_only=True)
    specialties_ids = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(), many=True, write_only=True, source='specialties'
    )

    class Meta:
        model = Doctor
        fields = [
            'id', 'npi', 'name', 'email', 'phone_number',
            'specialties', 'specialties_ids',
            'affiliated_clinics', 'affiliated_patients'
        ]

    def get_affiliated_patients(self, obj):
        appointment_patient_ids = Appointment.objects.filter(doctor=obj).values_list('patient_id', flat=True)
        visit_patient_ids = Visit.objects.filter(doctor=obj).values_list('patient_id', flat=True)
        total_patient_ids = set(list(appointment_patient_ids) + list(visit_patient_ids))
        return len(total_patient_ids)

    def create(self, validated_data):
        specialties = validated_data.pop('specialties', [])
        doctor = Doctor.objects.create(**validated_data)
        doctor.specialties.set(specialties)
        return doctor

    def update(self, instance, validated_data):
        specialties = validated_data.pop('specialties', None)
        instance.npi = validated_data.get('npi', instance.npi)
        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        if specialties is not None:
            instance.specialties.set(specialties)
        return instance

class VisitSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True) 
    clinic_name = serializers.CharField(source='clinic.name', read_only=True) 
    doctors_notes = serializers.CharField(allow_blank=True)

    class Meta:
        model = Visit
        fields = ['id', 'patient', 'doctor_name', 'clinic_name', 'visit_date', 'procedures_done', 'doctors_notes']

class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)
    procedure_display = serializers.CharField(source='get_procedure_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'doctor_name', 'clinic', 'clinic_name', 'appointment_date', 'procedure', 'procedure_display', 'status', 'status_display', 'date_booked']

class PatientSerializer(serializers.ModelSerializer):
    visits = VisitSerializer(many=True, read_only=True)
    last_visit_date = serializers.SerializerMethodField()
    last_visit_doctor = serializers.SerializerMethodField()
    last_visit_procedures = serializers.SerializerMethodField()
    next_appointment_date = serializers.SerializerMethodField()
    next_appointment_doctor = serializers.SerializerMethodField()
    next_appointment_procedure = serializers.SerializerMethodField()
    next_appointment_clinic = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'name', 'address', 'phone_number', 'date_of_birth', 'ssn_last4', 'gender',
                  'last_visit_date', 'last_visit_doctor', 'last_visit_procedures',
                  'next_appointment_date', 'next_appointment_doctor', 'next_appointment_clinic',
                  'next_appointment_procedure', 'visits']

    def get_last_visit_date(self, obj):
        last_visit = obj.visits.order_by('-visit_date').first()
        return last_visit.visit_date if last_visit else None

    def get_last_visit_doctor(self, obj):
        last_visit = obj.visits.order_by('-visit_date').first()
        return last_visit.doctor.name if last_visit else None

    def get_last_visit_procedures(self, obj):
        last_visit = obj.visits.order_by('-visit_date').first()
        return last_visit.procedures_done if last_visit else None

    def get_next_appointment_date(self, obj):
        now = timezone.now()
        next_appointment = obj.appointments.filter(
            status=AppointmentStatusChoices.SCHEDULED,
            appointment_date__gte=now
        ).order_by('appointment_date').first()
        return next_appointment.appointment_date if next_appointment else None

    def get_next_appointment_doctor(self, obj):
        now = timezone.now()
        next_appointment = obj.appointments.filter(
            status=AppointmentStatusChoices.SCHEDULED,
            appointment_date__gte=now
        ).order_by('appointment_date').first()
        return next_appointment.doctor.name if next_appointment else None

    def get_next_appointment_procedure(self, obj):
        now = timezone.now()
        next_appointment = obj.appointments.filter(
            status=AppointmentStatusChoices.SCHEDULED,
            appointment_date__gte=now
        ).order_by('appointment_date').first()
        return next_appointment.procedure if next_appointment else None

    def get_next_appointment_clinic(self, obj):
        now = timezone.now()
        next_appointment = obj.appointments.filter(
            status=AppointmentStatusChoices.SCHEDULED,
            appointment_date__gte=now
        ).order_by('appointment_date').first()
        return next_appointment.clinic.name if next_appointment else None

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.address = validated_data.get('address', instance.address)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.ssn_last4 = validated_data.get('ssn_last4', instance.ssn_last4)
        instance.save()
        return instance
