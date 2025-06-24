from django.db import models
from users.models import User


class Patient(models.Model):
    """
    Patient model with basic demographics
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    medical_record_number = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    blood_type = models.CharField(max_length=5, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.medical_record_number}"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def phone(self):
        return self.user.phone
    
    @property
    def date_of_birth(self):
        return self.user.date_of_birth
