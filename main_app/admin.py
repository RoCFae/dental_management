from django.contrib import admin
from .models import Clinic, Doctor, Patient

admin.site.register(Clinic)
admin.site.register(Doctor)
admin.site.register(Patient)
