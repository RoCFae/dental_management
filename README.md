# Bright Smile Dental Systems Management Platform

## Introduction

Welcome to the Bright Smile Dental Systems Management Platform. This application is designed to help administrative employees efficiently manage clinics, doctors, and patients across multiple locations in the United States. With this platform, users can schedule appointments, track visits, and handle affiliations between doctors and clinics—all through an intuitive web interface.

## Features

- **User Authentication**: Secure login using email and password.
- **Clinics Management**:
  - View, add, and edit clinics.
  - Display clinic details, including affiliated doctors and patients.
  - Manage doctor affiliations, including office address and working schedules.
- **Doctors Management**:
  - View, add, and edit doctors.
  - Display doctor details, specialties, clinics, and affiliated patients.
- **Patients Management**:
  - View, add, and edit patients.
  - Display patient details, visit history, and upcoming appointments.
  - Schedule new appointments and add visits.
- **Appointment Scheduling**:
  - Schedule appointments based on procedure, clinic, doctor availability, and working schedule.
  - Prevent scheduling conflicts with existing appointments.
- **REST API Endpoints**:
  - Add Patient
  - Add Doctor
  - Add Clinic
  - Get Clinic Information

## Technologies Used

- Backend: Django (Python)
- Frontend: HTML, Bootstrap, JavaScript
- Database: PostgreSQL
- API Framework: Django REST Framework

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Setup](#setup)
4. [Running the Application](#running-the-application)
5. [Usage](#usage)
6. [Using the Web Interface](#using-the-web-interface)
7. [Using the REST API](#using-the-rest-api)
8. [Testing](#testing)
9. [Assumptions](#assumptions)
10. [Configuration](#configuration)
11. [Known Issues](#known-issues)
12. [Future Improvements](#future-improvements)
13. [License](#license)
14. [Acknowledgements](#acknowledgements)

## Requirements

- Python: 3.8 or higher
- Django: 3.x or higher
- PostgreSQL: 10 or higher
- Git: For cloning the repository

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/bright-smile-dental.git
   cd bright-smile-dental
   ```

2. **Set Up Virtual Environment**
   It is recommended to use a virtual environment to manage Python dependencies.

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scriptsctivate`
   ```

3. **Install Python Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up the Database**
   Ensure that PostgreSQL is installed and running.
   Create a new PostgreSQL database:

   ```bash
   sudo -u postgres psql
   ```

   In the PostgreSQL shell:

   ```sql
    CREATE DATABASE dental_management_db;
    CREATE USER yourusername WITH PASSWORD 'yourpassword';
    ALTER ROLE yourusername SET client_encoding TO 'utf8';
    ALTER ROLE yourusername SET default_transaction_isolation TO 'read committed';
    ALTER ROLE yourusername SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE dental_management_db TO yourusername;
    \q
   ```

   Update the DATABASES setting in settings.py:

   ```python
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'dental_management_db',
            'USER': 'yourusername',
            'PASSWORD': 'yourpassword',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
   ```

5. **Apply Migrations**

   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser**

   ```bash
   python manage.py createsuperuser
   ```

7. **Collect Static Files**
   ```bash
   python manage.py collectstatic
   ```

## Setup

Before running the application, ensure all environment variables and configurations are correctly set.

- **Secret Key**: Update the SECRET_KEY in settings.py for production use.
- **Allowed Hosts**: Add your domain or IP address to ALLOWED_HOSTS in settings.py.
- **CSRF Trusted Origins**: Update CSRF_TRUSTED_ORIGINS if accessing the app from a different domain.

## Running the Application

1. **Start the Development Server**

   ```bash
   python manage.py runserver
   ```

2. **Access the Application**
   Open your web browser and navigate to `http://127.0.0.1:8000/`.
   Log in using the superuser credentials you created earlier.

## Usage

### Using the Web Interface

Once logged in, you can access the main features of the platform through the navigation tabs: Clinics, Doctors, and Patients.

### Clinics Management

- **View Clinics**: Access a list of clinics with details like name, phone number, city, state, and counts of affiliated doctors and patients.
- **Add Clinic**: Click on the "Add Clinic" button to create a new clinic.
- **Edit Clinic**: Click on a clinic name to view and edit its details, including address and email.
- **Manage Doctor Affiliations**: Add, edit, or remove doctor affiliations from a clinic.

### Doctors Management

- **View Doctors**: Access a list of doctors with details like NPI, name, specialties, and counts of affiliated clinics and patients.
- **Add Doctor**: Click on the "Add Doctor" button to create a new doctor, including selecting specialties from a predefined list.
- **Edit Doctor**: Click on a doctor's name to view and edit their information.

### Patients Management

- **View Patients**: Access a list of patients with details like name, date of birth, last visit date, and upcoming appointments.
- **Add Patient**: Click on the "Add Patient" button to create a new patient.
- **Edit Patient**: Click on a patient's name to view and edit their information.

### Appointment Scheduling

- Select procedure, clinic, doctor, and time slot.
- Schedule appointments based on availability and prevent conflicts.

### Using the REST API

The platform exposes several REST API endpoints:

- **Add Patient**: `POST /api/patients/`
- **Add Doctor**: `POST /api/doctors/`
- **Add Clinic**: `POST /api/clinics/`
- **Get Clinic Information**: `GET /api/clinics/<clinic_id>/`

## Testing

To run the tests:

```bash
python manage.py test
```

## Assumptions

- **User Management**: Managed via Django admin or the `createsuperuser` command.
- **Time Zones**: All times are stored in UTC.
- **Working Schedule Format**: Stored as a JSON field.

## Configuration

- Update `DATABASES` in `settings.py` with PostgreSQL credentials.
- Adjust `STATIC_URL` and `STATICFILES_DIRS` for serving static files.

## Known Issues

- **Time Zone Handling**: Users in different time zones may experience inconsistencies.
- **Error Handling**: Limited error handling is implemented.

## Future Improvements

- Enhanced UI/UX, user roles, notifications, and performance optimization.

## License

This project is licensed under the MIT License.

## Acknowledgements

- Django, Django REST Framework, Bootstrap.
