from django.contrib import admin
from .models import MedicalRecord


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'visit_date', 'diagnosis', 'follow_up_required', 'created_at')
    list_filter = ('visit_date', 'follow_up_required', 'doctor__specialization', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'diagnosis', 'symptoms')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-visit_date',)
    date_hierarchy = 'visit_date'
    
    fieldsets = (
        ('Visit Information', {
            'fields': ('patient', 'doctor', 'visit_date')
        }),
        ('Medical Assessment', {
            'fields': ('symptoms', 'diagnosis', 'vital_signs')
        }),
        ('Treatment', {
            'fields': ('treatment_notes', 'medications_prescribed')
        }),
        ('Results & Follow-up', {
            'fields': ('lab_results', 'imaging_results', 'follow_up_required', 'follow_up_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
