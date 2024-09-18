from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect

from main_app.forms import LoginForm
from .models import Clinic, Doctor, Patient, Visit, DoctorAffiliation, Specialty, Appointment, AppointmentStatusChoices
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import ClinicSerializer, DoctorSerializer, PatientSerializer, VisitSerializer, DoctorAffiliationSerializer, SpecialtySerializer, AppointmentSerializer
from django.db import transaction
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
import json

# ensures that only authenticated users can access these views
@method_decorator(login_required, name='dispatch')
class ClinicViewSet(viewsets.ModelViewSet):
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer

    # override the default queryset to filter clinics based on a procedure
    def get_queryset(self):
        procedure = self.request.query_params.get('procedure', None)
        if procedure:
            # filters clinics that have doctors with the specified specialty
            return Clinic.objects.filter(affiliations__doctor__specialties__name=procedure).distinct()
        return super().get_queryset()

    # custom action to list doctors affiliated with a specific clinic
    @action(detail=True, methods=['get'])
    def doctors(self, request, pk=None):
        clinic = self.get_object() 
        affiliations = DoctorAffiliation.objects.filter(clinic=clinic)
        
        serializer = DoctorAffiliationSerializer(affiliations, many=True)
        return Response(serializer.data)

    # custom action to add a new doctor affiliation to a clinic
    @action(detail=True, methods=['post'], url_path='add_affiliation')
    def add_affiliation(self, request, pk=None):
        clinic = self.get_object()  # Fetch the clinic.
        data = request.data
        doctor_id = data.get('doctor_id')

        # prevent duplicate affiliations between the same doctor and clinic
        if DoctorAffiliation.objects.filter(doctor_id=doctor_id, clinic=clinic).exists():
            return Response({'error': 'Doctor is already affiliated with this clinic.'}, status=status.HTTP_400_BAD_REQUEST)

        # check if the doctor exists
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)

        # create the new affiliation
        DoctorAffiliation.objects.create(
            doctor=doctor,
            clinic=clinic,
            office_address=data.get('office_address'),
            working_schedule=data.get('working_schedule')
        )

        return Response({'message': 'Affiliation created successfully'}, status=status.HTTP_201_CREATED)

    # custom action to edit an existing doctor affiliation
    @action(detail=True, methods=['put'], url_path=r'edit_affiliation/(?P<doctor_id>\d+)')
    def edit_affiliation(self, request, pk=None, doctor_id=None):
        clinic = self.get_object()  # Fetch the clinic.
        data = request.data

        # find the specific affiliation between the doctor and clinic
        affiliation = DoctorAffiliation.objects.filter(doctor_id=doctor_id, clinic=clinic).first()

        if not affiliation:
            return Response({'error': 'Affiliation not found'}, status=status.HTTP_404_NOT_FOUND)

        # update the affiliation details 
        affiliation.office_address = data.get('office_address')
        affiliation.working_schedule = data.get('working_schedule')
        affiliation.save()

        return Response({'message': 'Affiliation updated successfully'}, status=status.HTTP_200_OK)

    # custom action to remove a doctor affiliation
    @action(detail=True, methods=['delete'], url_path=r'remove_affiliation/(?P<doctor_id>\d+)')
    def remove_affiliation(self, request, pk=None, doctor_id=None):
        clinic = self.get_object()
        try:
            # find and delete the affiliation
            affiliation = DoctorAffiliation.objects.get(clinic=clinic, doctor_id=doctor_id)
            affiliation.delete()
            return Response({'message': 'Affiliation removed successfully'}, status=status.HTTP_200_OK)
        except DoctorAffiliation.DoesNotExist:
            return Response({'error': 'Affiliation not found'}, status=status.HTTP_404_NOT_FOUND)


# ViewSet for managing doctors
@method_decorator(login_required, name='dispatch')
class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    # custom action to fetch available time slots for a doctor at a specific clinic
    @action(detail=True, methods=['get'], url_path='available_time_slots')
    def available_time_slots(self, request, pk=None):
        try:
            doctor = self.get_object() 
        except Doctor.DoesNotExist:
            return Response({"detail": "No Doctor matches the given query."}, status=404)

        clinic_id = request.query_params.get('clinic_id', None)
        if clinic_id:
            affiliations = DoctorAffiliation.objects.filter(clinic_id=clinic_id, doctor=doctor)
            if affiliations.exists():
                affiliation = affiliations.first()
                working_schedule = affiliation.working_schedule

                # ensure the working schedule is in the correct format
                if isinstance(working_schedule, str):
                    try:
                        working_schedule_dict = json.loads(working_schedule)
                    except json.JSONDecodeError:
                        return Response({"detail": "Error decoding working schedule."}, status=500)
                else:
                    working_schedule_dict = working_schedule

                return Response(working_schedule_dict, status=200)
            return Response({"detail": "No affiliations found for this doctor at the specified clinic."}, status=404)

        return Response({"detail": "Clinic ID not provided."}, status=400)


# ViewSet for managing patients
@method_decorator(login_required, name='dispatch')
class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

    @action(detail=True, methods=['post'], url_path='schedule_appointment')
    def schedule_appointment(self, request, pk=None):
        patient = get_object_or_404(Patient, pk=pk)
        data = request.data

        doctor_id = data.get('doctor_id')
        clinic_id = data.get('clinic_id')
        appointment_date = data.get('appointment_date')
        procedure = data.get('procedure')

        doctor = get_object_or_404(Doctor, id=doctor_id)
        clinic = get_object_or_404(Clinic, id=clinic_id)

        try:
            appointment_datetime = datetime.strptime(appointment_date, "%Y-%m-%d %H:%M")
        except ValueError:
            return Response({"error": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)

        time_window_start = appointment_datetime - timedelta(minutes=30)
        time_window_end = appointment_datetime + timedelta(minutes=30)

        with transaction.atomic():
            conflicting_appointment = Appointment.objects.filter(
                doctor=doctor,
                clinic=clinic,
                appointment_date__range=(time_window_start, time_window_end),
                status=AppointmentStatusChoices.SCHEDULED
            ).exists()

            if conflicting_appointment:
                return Response(
                    {'error': 'This doctor already has an appointment within 30 minutes of the selected time.'},
                    status=status.HTTP_409_CONFLICT
                )

            conflicting_patient_appointment = Appointment.objects.filter(
                patient=patient,
                doctor=doctor,
                clinic=clinic,
                appointment_date=appointment_datetime,
                status=AppointmentStatusChoices.SCHEDULED
            ).exists()

            if conflicting_patient_appointment:
                return Response(
                    {'error': 'This patient already has an appointment with this doctor at the selected time.'},
                    status=status.HTTP_409_CONFLICT
                )

            # Criar o novo agendamento
            Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                clinic=clinic,
                appointment_date=appointment_datetime,
                procedure=procedure,
                status=AppointmentStatusChoices.SCHEDULED
            )

        return Response({'message': 'Appointment scheduled successfully!'}, status=status.HTTP_201_CREATED)

@method_decorator(login_required, name='dispatch')
class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_appointment(self, request, pk=None):
        appointment = get_object_or_404(Appointment, pk=pk)
        if appointment.status != AppointmentStatusChoices.SCHEDULED:
            return Response({'error': 'Appointment is not scheduled or already completed.'}, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data
        doctors_notes = data.get('doctors_notes', '')

        # Criar uma Visita
        Visit.objects.create(
            patient=appointment.patient,
            doctor=appointment.doctor,
            clinic=appointment.clinic,
            visit_date=appointment.appointment_date,
            procedures_done=appointment.procedure,
            doctors_notes=doctors_notes
        )

        # Atualizar o status do agendamento
        appointment.status = AppointmentStatusChoices.COMPLETED
        appointment.save()

        return Response({'message': 'Appointment completed and visit recorded.'}, status=status.HTTP_200_OK)


# ViewSet for managing visits
@method_decorator(login_required, name='dispatch')
class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer
    
    def perform_create(self, serializer):
        visit = serializer.save()

        patient = visit.patient
        patient.last_visit_date = visit.visit_date
        patient.last_visit_doctor = visit.doctor
        patient.last_visit_procedures = visit.procedures_done
        patient.save()


# custom login view that redirects authenticated users to the clinic page
class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'main_app/registration/login.html' 

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('main_app/clinics/clinics.html') 
        return super().dispatch(request, *args, **kwargs)


# ViewSet for managing Specialties
@method_decorator(login_required, name='dispatch')
class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer


# custom view for listing clinics
@login_required
def clinics_view(request):
    return render(request, 'main_app/clinics/clinics.html')

# custom view for listing doctors
@login_required
def doctors_view(request):
    return render(request, 'main_app/doctors/doctors.html')

# custom view for listing patients
@login_required
def patients_view(request):
    return render(request, 'main_app/patients/patients.html')

# detailed view of a clinic, including affiliated doctors
@login_required
def clinic_detail_view(request, pk):
    clinic = get_object_or_404(Clinic, pk=pk)
    doctors = Doctor.objects.filter(affiliations__clinic=clinic).prefetch_related('affiliations').distinct()

    for doctor in doctors:
        for affiliation in doctor.affiliations.all():
            if affiliation.working_schedule:
                affiliation.working_schedule = json.dumps(affiliation.working_schedule)

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    return render(request, 'main_app/clinics/clinic_detail.html', {
        'clinic': clinic,
        'doctors': doctors,
        'days_of_week': days_of_week
    })

# detailed view of a doctor, including their affiliations and patients
@login_required
def doctor_detail_view(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    affiliations = doctor.affiliations.all()
    patients = doctor.patients.all()
    all_specialties = Specialty.objects.all()

    return render(request, 'main_app/doctors/doctor_detail.html', {
        'doctor': doctor,
        'affiliations': affiliations,
        'patients': patients,
        'all_specialties': all_specialties,
    })

# detailed view of a patient, including their visit history
@login_required
def patient_detail_view(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    serializer = PatientSerializer(patient)
    patient_data = serializer.data
    return render(request, 'main_app/patients/patient_detail.html', {
        'patient': patient_data,
    })
