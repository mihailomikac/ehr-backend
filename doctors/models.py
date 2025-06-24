from django.db import models
from users.models import User


class Doctor(models.Model):
    """
    Doctor model with specialization and contact information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=20, unique=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    education = models.TextField(blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)
    office_location = models.CharField(max_length=200, blank=True, null=True)
    office_hours = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'doctors'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def phone(self):
        return self.user.phone
