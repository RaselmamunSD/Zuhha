from django.contrib import admin
from .models import Mosque, MosqueImage


@admin.register(Mosque)
class MosqueAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'address', 'phone', 'is_verified', 'is_active', 'capacity', 'created_at']
    list_filter = ['is_verified', 'is_active', 'has_parking', 'has_wudu_area', 'has_women_facility', 'has_jumuah', 'has_quran_classes', 'has_ramadan_iftar', 'city__country']
    search_fields = ['name', 'address', 'city__name', 'phone', 'email']
    list_editable = ['is_verified', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'city', 'address', 'phone', 'email', 'website')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Facilities', {
            'fields': ('has_parking', 'has_wudu_area', 'has_women_facility', 'has_jumuah', 'has_quran_classes', 'has_ramadan_iftar')
        }),
        ('Capacity', {
            'fields': ('capacity',)
        }),
        ('Prayer Times (Jamaah)', {
            'fields': ('fajr_jamaah', 'dhuhr_jamaah', 'asr_jamaah', 'maghrib_jamaah', 'isha_jamaah', 'jumuah_khutbah')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MosqueImage)
class MosqueImageAdmin(admin.ModelAdmin):
    list_display = ['mosque', 'caption', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'mosque__city__country']
    search_fields = ['mosque__name', 'caption']
    list_editable = ['is_primary', 'caption']

