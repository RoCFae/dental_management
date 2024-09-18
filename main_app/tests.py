from rest_framework.test import APITestCase
from django.urls import reverse
from main_app.models import Clinic, Doctor, Patient, Visit
from datetime import datetime
from rest_framework import status
from django.contrib.auth.models import User

# this test case checks for appointment scheduling conflicts.
class AppointmentConflictTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345') 

        # create example data: a clinic, a doctor, a patient, and a scheduled appointment
        self.clinic = Clinic.objects.create(
            name="Dental Clinic",
            city="New York",
            state="NY"
        )
        self.doctor = Doctor.objects.create(
            name="Dr. Smith",
            npi="1234567890",
            email="drsmith@example.com"
        )
        self.patient = Patient.objects.create(
            name="John Doe",
            date_of_birth="1980-01-01"
        )
        self.appointment_datetime = "2024-09-18 10:00"

        # create a first appointment to create a conflict scenario later
        self.first_appointment = Visit.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            clinic=self.clinic,
            visit_date=self.appointment_datetime,
            procedures_done="Cleaning"
        )

        self.url = reverse('patient-schedule-appointment', kwargs={'pk': self.patient.id})

    # test case for handling appointment conflicts
    def test_appointment_conflict(self):
        # data for a second appointment that will create a conflict
        data = {
            "procedure": "Filling",
            "clinic_id": self.clinic.id,
            "doctor_id": self.doctor.id,
            "appointment_date": self.appointment_datetime  # same time as the first appointment
        }

        response = self.client.post(self.url, data, format='json')

        # check if the response status is 409 and if the error message matches
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'This doctor already has an appointment within 30 minutes of the selected time.')

    # test case for scheduling an appointment without conflicts
    def test_appointment_without_conflict(self):
        # data for a second appointment without conflict (different time)
        data = {
            "procedure": "Filling",
            "clinic_id": self.clinic.id,
            "doctor_id": self.doctor.id,
            "appointment_date": "2024-09-18 11:00" 
        }

        # make a POST request to schedule the non-conflicting appointment
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Appointment scheduled successfully!')


# this test case covers the API functionalities for the clinic model
class ClinicAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345') 

        # create an example clinic
        self.clinic = Clinic.objects.create(
            name="Dental Clinic",
            city="New York",
            state="NY"
        )

    # test case for listing clinics
    def test_list_clinics(self):
        response = self.client.get(reverse('clinic-list')) 

        # check if the response status is 200 (OK) and if at least one clinic is returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)  

    # test case for creating a new clinic
    def test_create_clinic(self):
        data = {
            "name": "New Clinic",
            "city": "Los Angeles",
            "state": "CA",
            "phone_number": "0123456789"
        }

        response = self.client.post(reverse('clinic-list'), data, format='json')

        # check if the response status is 201 
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# this test case covers API functionalities for the patient model
class PatientAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345') 

        # create example data
        self.clinic = Clinic.objects.create(
            name="Dental Clinic",
            city="New York",
            state="NY"
        )
        self.doctor = Doctor.objects.create(
            name="Dr. Smith",
            npi="1234567890",
            email="drsmith@example.com"
        )
        self.patient = Patient.objects.create(
            name="John Doe",
            date_of_birth="1980-01-01"
        )

    # test case for invalid appointment data
    def test_appointment_invalid_data(self):
        invalid_data = {
            "procedure": "",  
            "clinic_id": self.clinic.id,
            "doctor_id": self.doctor.id,
            "appointment_date": "invalid_date" 
        }

        # make a POST request with invalid data
        url = reverse('patient-schedule-appointment', kwargs={'pk': self.patient.id})
        response = self.client.post(url, invalid_data, format='json')

        # check if the response status is 400 (Bad Request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# this test case covers API functionalities for the doctor model
class DoctorAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')  

        # create example data: a clinic and a doctor
        self.clinic = Clinic.objects.create(
            name="Dental Clinic",
            city="New York",
            state="NY"
        )
        self.doctor = Doctor.objects.create(
            name="Dr. Smith",
            npi="1234567890",
            email="drsmith@example.com"
        )
