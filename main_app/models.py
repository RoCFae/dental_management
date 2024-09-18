from django.db import models
from django.core.exceptions import ValidationError
import json
from datetime import datetime

class SpecialtyChoices(models.TextChoices):
    CLEANING = 'Cleaning', 'Cleaning'
    FILLING = 'Filling', 'Filling'
    ROOT_CANAL = 'Root Canal', 'Root Canal'
    CROWN = 'Crown', 'Crown'
    TEETH_WHITENING = 'Teeth Whitening', 'Teeth Whitening'

class GenderChoices(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female'
    OTHER = 'O', 'Other' 

class AppointmentStatusChoices(models.TextChoices):
    SCHEDULED = 'Scheduled', 'Scheduled'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'

class Specialty(models.Model):
    name = models.CharField(max_length=50, choices=SpecialtyChoices.choices)

    def __str__(self):
        return self.name 

class Clinic(models.Model):
    name = models.CharField(max_length=255, unique=True)  
    phone_number = models.CharField(max_length=20) 
    city = models.CharField(max_length=100)  
    state = models.CharField(max_length=50)  
    address = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True) 

    def __str__(self):
        return self.name

class DoctorAffiliation(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='affiliations')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='affiliations')
    
    office_address = models.CharField(max_length=255)
    working_schedule = models.JSONField()

    class Meta:
        unique_together = ('doctor', 'clinic')

    def __str__(self):
        return f"{self.doctor.name} affiliated with {self.clinic.name}"

    def clean(self):
        super().clean()
        if self.working_schedule:
            if isinstance(self.working_schedule, str):
                try:
                    schedule = json.loads(self.working_schedule)
                except json.JSONDecodeError:
                    raise ValidationError("Invalid JSON format for working schedule.")
            else:
                schedule = self.working_schedule
            for day, times in schedule.items():
                if len(times) != 2:
                    raise ValidationError(f"Invalid time format for {day}. Expected two time values (start and end).")
                start_time_str, end_time_str = times
                try:
                    start_time = datetime.strptime(start_time_str, '%H:%M')
                    end_time = datetime.strptime(end_time_str, '%H:%M')
                except ValueError:
                    raise ValidationError(f"Invalid time format for {day}. Expected 'HH:MM'.")
                if start_time >= end_time:
                    raise ValidationError(f"Invalid time interval for {day}. Start time must be earlier than end time.")
        else:
            raise ValidationError("Working schedule cannot be empty.") 

class Doctor(models.Model):
    npi = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(default='notprovided@example.com', unique=True) 
    phone_number = models.CharField(max_length=20, null=True, blank=True) 
    specialties = models.ManyToManyField(Specialty)

    def __str__(self):
        return self.name 

class Patient(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True, unique=True) 
    date_of_birth = models.DateField()
    ssn_last4 = models.CharField(max_length=4, default='0000')  
    gender = models.CharField(max_length=1, choices=GenderChoices.choices, default=GenderChoices.OTHER)

    def __str__(self):
        return self.name  

class Visit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='visits')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    visit_date = models.DateTimeField() 
    procedures_done = models.CharField(max_length=255) 
    doctors_notes = models.TextField() 

    def __str__(self):
        return f"Visit for {self.patient.name} on {self.visit_date}" 

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField()
    procedure = models.CharField(max_length=50, choices=SpecialtyChoices.choices)
    status = models.CharField(max_length=20, choices=AppointmentStatusChoices.choices, default=AppointmentStatusChoices.SCHEDULED)
    date_booked = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment for {self.patient.name} with {self.doctor.name} on {self.appointment_date}"
