from django.contrib import admin
from .models import Country, City


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone_code', 'currency', 'currency_symbol', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'currency']
    list_editable = ['is_active']
    ordering = ['name']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'latitude', 'longitude', 'timezone', 'elevation', 'is_capital', 'is_active', 'created_at']
    list_filter = ['is_capital', 'is_active', 'country']
    search_fields = ['name', 'country__name', 'timezone']
    list_editable = ['is_capital', 'is_active', 'timezone', 'elevation']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']

