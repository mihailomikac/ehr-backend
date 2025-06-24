from django.db import models
from patients.models import Patient
from doctors.models import Doctor


class MedicalRecord(models.Model):
    """
    Medical record model for patient visit documentation
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='medical_records')
    visit_date = models.DateTimeField()
    diagnosis = models.TextField()
    treatment_notes = models.TextField()
    symptoms = models.TextField(blank=True, null=True)
    vital_signs = models.JSONField(blank=True, null=True)  # Blood pressure, temperature, etc.
    medications_prescribed = models.TextField(blank=True, null=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    lab_results = models.TextField(blank=True, null=True)
    imaging_results = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medical_records'
        ordering = ['-visit_date']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.visit_date.strftime('%Y-%m-%d')} - {self.diagnosis[:50]}..."
    
    @property
    def is_recent(self):
        from django.utils import timezone
        from datetime import timedelta
        return self.visit_date > timezone.now() - timedelta(days=30)
