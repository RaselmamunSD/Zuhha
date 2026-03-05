from django.contrib import admin
from .models import Country, City
from unfold.admin import ModelAdmin

@admin.register(Country)
class CountryAdmin(ModelAdmin):
    list_display = ['name', 'code', 'phone_code', 'currency', 'currency_symbol', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'currency']
    list_editable = ['is_active']
    ordering = ['name']
    
    def has_module_permission(self, request):
        """Hide from Imam users."""
        if request.user.is_superuser:
            return True
        return not request.user.groups.filter(name='Imam').exists()


@admin.register(City)
class CityAdmin(ModelAdmin):
    list_display = ['name', 'country', 'latitude', 'longitude', 'timezone', 'elevation', 'is_capital', 'is_active', 'created_at']
    list_filter = ['is_capital', 'is_active', 'country']
    search_fields = ['name', 'country__name', 'timezone']
    list_editable = ['is_capital', 'is_active', 'timezone', 'elevation']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_module_permission(self, request):
        """Hide from Imam users."""
        if request.user.is_superuser:
            return True
        return not request.user.groups.filter(name='Imam').exists()

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

