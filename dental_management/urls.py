from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from main_app.views import ClinicViewSet, DoctorViewSet, PatientViewSet, VisitViewSet, CustomLoginView, SpecialtyViewSet, AppointmentViewSet
from main_app import views
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

router = DefaultRouter()
router.register(r'clinics', ClinicViewSet, basename='clinic')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'visits', VisitViewSet, basename='visit')
router.register(r'specialties', SpecialtyViewSet)
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', RedirectView.as_view(url='login/', permanent=False), name='home'),

    path('login/', CustomLoginView.as_view(), name='login'),
    path('admin/', admin.site.urls),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('api/', include(router.urls)),
    path('clinics/', views.clinics_view, name='clinics'),
    path('api/clinics/<int:pk>/doctors/', ClinicViewSet.as_view({'get': 'doctors'})),
    path('api/doctors/<int:pk>/available_time_slots/', DoctorViewSet.as_view({'get': 'available_time_slots'})),
    path('doctors/', views.doctors_view, name='doctors'),
    path('patients/', views.patients_view, name='patients'),
    path('clinics/<int:pk>/', views.clinic_detail_view, name='clinic-detail'),
    path('patients/<int:pk>/', views.patient_detail_view, name='patient-detail'),
    path('doctors/<int:pk>/', views.doctor_detail_view, name='doctor-detail'),
]
