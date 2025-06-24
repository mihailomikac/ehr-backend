from django.db import models
from patients.models import Patient
from doctors.models import Doctor


class Appointment(models.Model):
    """
    Appointment model for scheduling patient visits
    """
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        NO_SHOW = 'NO_SHOW', 'No Show'
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    notes = models.TextField(blank=True, null=True)
    reason_for_visit = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointments'
        ordering = ['appointment_date']
        unique_together = ['doctor', 'appointment_date']
    
    def __str__(self):
        return f"{self.patient.full_name} with Dr. {self.doctor.full_name} on {self.appointment_date.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.appointment_date > timezone.now() and self.status in [self.Status.SCHEDULED, self.Status.CONFIRMED]
    
    @property
    def is_past(self):
        from django.utils import timezone
        return self.appointment_date < timezone.now()
