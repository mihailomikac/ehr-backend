from django.contrib import admin
from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('license_number', 'full_name', 'specialization', 'email', 'phone', 'years_of_experience', 'created_at')
    list_filter = ('specialization', 'years_of_experience', 'created_at')
    search_fields = ('license_number', 'user__first_name', 'user__last_name', 'user__email', 'specialization')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'specialization', 'license_number')
        }),
        ('Professional Information', {
            'fields': ('years_of_experience', 'education', 'certifications')
        }),
        ('Office Information', {
            'fields': ('office_location', 'office_hours')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
