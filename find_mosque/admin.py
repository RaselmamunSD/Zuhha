from django.contrib import admin
from django import forms
from django.db import models as db_models
from datetime import time as dt_time
from .models import Mosque, MosqueImage, FavoriteMosque, MosqueMonthlyPrayerTime
from unfold.admin import ModelAdmin


# ─── AM/PM Time Widget ──────────────────────────────────────────────────────

_INPUT_STYLE = (
    'display:inline-block;'
    'width:75px;'
    'padding:6px 10px;'
    'border:1px solid #d1d5db;'
    'border-radius:6px 0 0 6px;'
    'font-size:14px;'
    'text-align:center;'
    'outline:none;'
)

_SELECT_STYLE = (
    'display:inline-block;'
    'padding:6px 10px;'
    'border:1px solid #d1d5db;'
    'border-left:none;'
    'border-radius:0 6px 6px 0;'
    'font-size:14px;'
    'background:#f9fafb;'
    'cursor:pointer;'
    'outline:none;'
)


class TimeAMPMWidget(forms.MultiWidget):
    """Box-style time input — HH:MM text box + AM/PM dropdown."""

    def __init__(self, attrs=None):
        widgets = [
            forms.TextInput(attrs={'placeholder': 'HH:MM', 'style': _INPUT_STYLE}),
            forms.Select(
                choices=[('AM', 'AM'), ('PM', 'PM')],
                attrs={'style': _SELECT_STYLE},
            ),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        """Convert stored 24-hour time → [HH:MM 12h, AM/PM]."""
        if value:
            try:
                if hasattr(value, 'hour'):
                    hour, minute = value.hour, value.minute
                else:
                    parts = str(value).split(':')
                    hour, minute = int(parts[0]), int(parts[1])
                period = 'AM' if hour < 12 else 'PM'
                hour_12 = hour % 12 or 12
                return [f'{hour_12:02d}:{minute:02d}', period]
            except Exception:
                return ['', 'AM']
        return ['', 'AM']


class TimeAMPMField(forms.MultiValueField):
    """Field that pairs TimeAMPMWidget and converts back to 24-hour time."""
    widget = TimeAMPMWidget

    def __init__(self, *args, **kwargs):
        kwargs.pop('widget', None)
        fields = [
            forms.CharField(required=False),
            forms.ChoiceField(choices=[('AM', 'AM'), ('PM', 'PM')], required=False),
        ]
        super().__init__(fields=fields, require_all_fields=False, *args, **kwargs)
        self.widget = TimeAMPMWidget()

    def compress(self, data_list):
        if not data_list or not data_list[0]:
            return None
        time_str = str(data_list[0]).strip()
        period = (data_list[1] if len(data_list) > 1 and data_list[1] else 'AM').upper()
        try:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            if period == 'PM' and hour != 12:
                hour += 12
            elif period == 'AM' and hour == 12:
                hour = 0
            return dt_time(hour, minute)
        except (ValueError, IndexError):
            raise forms.ValidationError('Enter time as HH:MM, e.g. 05:30')


# ─── Monthly Prayer Time Form ───────────────────────────────────────────────

TIME_FIELDS = [
    'fajr_adhan', 'fajr_iqamah', 'sunrise',
    'dhuhr_adhan', 'dhuhr_iqamah',
    'asr_adhan', 'asr_iqamah',
    'maghrib_adhan', 'maghrib_iqamah',
    'isha_adhan', 'isha_iqamah',
]

TIME_HELP = {
    'fajr_adhan':    'Fajr Adhan — e.g. 05:10 AM',
    'fajr_iqamah':   'Fajr Iqamah — e.g. 05:30 AM',
    'sunrise':       'Sunrise — e.g. 06:15 AM',
    'dhuhr_adhan':   'Dhuhr Adhan — e.g. 01:00 PM',
    'dhuhr_iqamah':  'Dhuhr Iqamah — e.g. 01:20 PM',
    'asr_adhan':     'Asr Adhan — e.g. 04:30 PM',
    'asr_iqamah':    'Asr Iqamah — e.g. 04:45 PM',
    'maghrib_adhan': 'Maghrib Adhan — e.g. 06:45 PM',
    'maghrib_iqamah':'Maghrib Iqamah — e.g. 06:50 PM',
    'isha_adhan':    'Isha Adhan — e.g. 08:00 PM',
    'isha_iqamah':   'Isha Iqamah — e.g. 08:20 PM',
}


class MosqueMonthlyPrayerTimeForm(forms.ModelForm):
    """Monthly prayer time form with box + AM/PM dropdown for every time field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in TIME_FIELDS:
            if field_name in self.fields:
                original = self.fields[field_name]
                self.fields[field_name] = TimeAMPMField(
                    label=original.label,
                    required=original.required,
                    help_text=TIME_HELP.get(field_name, 'Enter time as HH:MM and select AM/PM'),
                )

    class Meta:
        model = MosqueMonthlyPrayerTime
        fields = '__all__'


# ─── Imam Mosque Form (city as plain text) ───────────────────────────────────

_FIELD_STYLE = (
    'width:100%;'
    'padding:10px 14px;'
    'border:1.5px solid #d1d5db;'
    'border-radius:8px;'
    'font-size:15px;'
    'background:#ffffff;'
    'box-sizing:border-box;'
    'outline:none;'
    'transition:border-color .2s;'
)

class ImamMosqueForm(forms.ModelForm):
    """
    Simplified form for Imam users.
    'city' ForeignKey is replaced by a plain text field.
    The actual City object is resolved in MosqueAdmin.save_model.
    """
    city_name = forms.CharField(
        max_length=200,
        label='City',
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter the city name. (For example: Dhaka, London, New York)',
            'style': _FIELD_STYLE,
        }),
        help_text='Enter the name of a city in any country.',
    )

    class Meta:
        model = Mosque
        fields = ['name', 'address']  # city handled via city_name in save_model
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter the mosque name.',
                'style': _FIELD_STYLE,
            }),
            'address': forms.Textarea(attrs={
                'placeholder': 'Enter the complete address.',
                'rows': 4,
                'style': _FIELD_STYLE + 'resize:vertical;',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill city_name when editing an existing mosque
        if self.instance and self.instance.pk and self.instance.city_id:
            self.fields['city_name'].initial = self.instance.city.name



@admin.register(Mosque)
class MosqueAdmin(ModelAdmin):
    PRAYER_TIME_FIELDS = (
        'fajr_beginning', 'sunrise', 'dhuhr_beginning', 'asr_beginning', 'maghrib_sunset', 'isha_beginning',
        'fajr_jamaah', 'dhuhr_jamaah', 'asr_jamaah', 'maghrib_jamaah', 'isha_jamaah', 'jumuah_khutbah',
    )
    
    IMAM_EDITABLE_FIELDS = (
        'name', 'address', 'city',  # Basic mosque info
        'fajr_beginning', 'sunrise', 'dhuhr_beginning', 'asr_beginning', 'maghrib_sunset', 'isha_beginning',
        'fajr_jamaah', 'dhuhr_jamaah', 'asr_jamaah', 'maghrib_jamaah', 'isha_jamaah', 'jumuah_khutbah',
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Use AM/PM widget for every TimeField on the Mosque form."""
        if isinstance(db_field, db_models.TimeField):
            return TimeAMPMField(
                label=db_field.verbose_name.capitalize(),
                required=not db_field.null,
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """Imam users get a simplified form with city as plain text input."""
        if not request.user.is_superuser and request.user.groups.filter(name='Imam').exists():
            return ImamMosqueForm
        return super().get_form(request, obj, **kwargs)

    list_display = ['name', 'created_by', 'contact_person', 'city', 'phone', 'is_verified', 'is_active', 'capacity', 'created_at']
    list_filter = ['is_verified', 'is_active', 'has_parking', 'has_wudu_area', 'has_women_facility', 'has_jumuah', 'has_quran_classes', 'has_ramadan_iftar', 'city__country']
    search_fields = ['name', 'contact_person', 'address', 'city__name', 'phone', 'email']
    list_editable = ['is_verified', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Imams can only see their own mosques; superusers see all."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter by created_by for Imam users
        return qs.filter(created_by=request.user)
    
    def has_module_permission(self, request):
        """Allow Imam group to access this module."""
        if request.user.is_superuser:
            return True
        # Check if user is in Imam group
        return request.user.groups.filter(name='Imam').exists()

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name='Imam').exists()

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name='Imam').exists()

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not request.user.groups.filter(name='Imam').exists():
            return False
        if obj is None:
            return True
        return obj.created_by_id == request.user.id
    
    def get_readonly_fields(self, request, obj=None):
        """Imams: on add, only name/city/address editable; on edit, also prayer times."""
        if request.user.is_superuser:
            return self.readonly_fields

        all_fields = [
            'name', 'created_by', 'contact_person', 'city', 'address', 'phone', 'email', 'website',
            'additional_info', 'latitude', 'longitude',
            'has_parking', 'has_wudu_area', 'has_women_facility', 'has_jumuah', 'has_quran_classes', 'has_ramadan_iftar',
            'capacity',
            'fajr_beginning', 'sunrise', 'dhuhr_beginning', 'asr_beginning', 'maghrib_sunset', 'isha_beginning',
            'fajr_jamaah', 'dhuhr_jamaah', 'asr_jamaah', 'maghrib_jamaah', 'isha_jamaah', 'jumuah_khutbah',
            'is_verified', 'is_active', 'created_at', 'updated_at',
        ]
        # When adding a new mosque, only allow name/city_name/address
        if obj is None:
            basic_fields = ('name', 'address')  # city handled via city_name text field
            return tuple(field for field in all_fields if field not in basic_fields)
        # When editing, allow name/city_name/address + prayer times
        imam_editable = [f for f in self.IMAM_EDITABLE_FIELDS if f != 'city']
        return tuple(field for field in all_fields if field not in imam_editable)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return self.fieldsets

        # ADD form: only basic mosque info
        if obj is None:
            return (
                ('Mosque Information', {
                    'fields': ('name', 'city_name', 'address'),
                    'description': 'Enter mosque name, area/district, and full address'
                }),
            )

        # EDIT form: basic info + prayer times
        return (
            ('Mosque Information', {
                'fields': ('name', 'city_name', 'address'),
                'description': 'Edit your mosque name, area/district, and full address'
            }),
            ('Prayer Times - Beginning (Azan/Start)', {
                'fields': ('fajr_beginning', 'sunrise', 'dhuhr_beginning', 'asr_beginning', 'maghrib_sunset', 'isha_beginning'),
            }),
            ('Prayer Times - Jamaah (Congregation)', {
                'fields': ('fajr_jamaah', 'dhuhr_jamaah', 'asr_jamaah', 'maghrib_jamaah', 'isha_jamaah', 'jumuah_khutbah'),
            }),
        )

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and request.user.groups.filter(name='Imam').exists():
            # Resolve city_name text → City object
            city_name = form.cleaned_data.get('city_name', '').strip()
            if city_name:
                from locations.models import City, Country
                city = City.objects.filter(name__iexact=city_name).first()
                if not city:
                    # Find or create a default country to attach the new city
                    country = Country.objects.filter(is_active=True).first()
                    if not country:
                        country, _ = Country.objects.get_or_create(
                            name='Bangladesh', defaults={'code': 'BGD'}
                        )
                    city, _ = City.objects.get_or_create(
                        name=city_name,
                        country=country,
                        defaults={'latitude': 0, 'longitude': 0, 'timezone': 'UTC'},
                    )
                obj.city = city
            if not obj.created_by_id:
                obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_list_editable(self, request):
        if request.user.is_superuser:
            return self.list_editable
        return []
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'created_by', 'contact_person', 'city', 'address', 'phone', 'email', 'website')
        }),
        ('Additional Information', {
            'fields': ('additional_info',)
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
        ('Prayer Times - Beginning (Azan/Start)', {
            'fields': ('fajr_beginning', 'sunrise', 'dhuhr_beginning', 'asr_beginning', 'maghrib_sunset', 'isha_beginning'),
            'description': 'Enter the beginning times for each prayer (when azan is called)'
        }),
        ('Prayer Times - Jamaah (Congregation)', {
            'fields': ('fajr_jamaah', 'dhuhr_jamaah', 'asr_jamaah', 'maghrib_jamaah', 'isha_jamaah', 'jumuah_khutbah'),
            'description': 'Enter the jamaah (congregation) times for each prayer'
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
class MosqueImageAdmin(ModelAdmin):
    list_display = ['mosque', 'caption', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'mosque__city__country']
    search_fields = ['mosque__name', 'caption']
    list_editable = ['is_primary', 'caption']
    
    def has_module_permission(self, request):
        """Hide from Imam users."""
        if request.user.is_superuser:
            return True
        return not request.user.groups.filter(name='Imam').exists()


@admin.register(FavoriteMosque)
class FavoriteMosqueAdmin(ModelAdmin):
    list_display = ['user', 'mosque', 'created_at']
    list_filter = ['created_at', 'mosque__city__country']
    search_fields = ['user__username', 'user__email', 'mosque__name', 'mosque__city__name']
    
    def has_module_permission(self, request):
        """Hide from Imam users."""
        if request.user.is_superuser:
            return True
        return not request.user.groups.filter(name='Imam').exists()


@admin.register(MosqueMonthlyPrayerTime)
class MosqueMonthlyPrayerTimeAdmin(ModelAdmin):
    form = MosqueMonthlyPrayerTimeForm
    list_display = ['mosque', 'year', 'month', 'day', 'fajr_adhan', 'fajr_iqamah', 'updated_at']
    list_filter = ['year', 'month', 'mosque__city__country']
    search_fields = ['mosque__name', 'mosque__city__name']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('mosque', 'year', 'month', 'day'),
            'description': 'Select your mosque and enter the date. Time format: You can type "05:45 AM" or "5:45 PM" or use 24-hour format "17:30"'
        }),
        ('Fajr Prayer Times', {
            'fields': ('fajr_adhan', 'fajr_iqamah'),
        }),
        ('Sunrise', {
            'fields': ('sunrise',),
        }),
        ('Dhuhr Prayer Times', {
            'fields': ('dhuhr_adhan', 'dhuhr_iqamah'),
        }),
        ('Asr Prayer Times', {
            'fields': ('asr_adhan', 'asr_iqamah'),
        }),
        ('Maghrib Prayer Times', {
            'fields': ('maghrib_adhan', 'maghrib_iqamah'),
        }),
        ('Isha Prayer Times', {
            'fields': ('isha_adhan', 'isha_iqamah'),
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter mosque dropdown for Imam users to show only their mosques."""
        if db_field.name == 'mosque':
            if not request.user.is_superuser and request.user.groups.filter(name='Imam').exists():
                kwargs['queryset'] = Mosque.objects.filter(created_by=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name='Imam').exists():
            return qs.filter(mosque__created_by=request.user)
        return qs.none()

    def has_module_permission(self, request):
        """Allow only superusers and Imam users."""
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name='Imam').exists()

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not request.user.groups.filter(name='Imam').exists():
            return False
        if obj is None:
            return True
        return obj.mosque.created_by_id == request.user.id

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name='Imam').exists()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not request.user.groups.filter(name='Imam').exists():
            return False
        if obj is None:
            return True
        return obj.mosque.created_by_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not request.user.groups.filter(name='Imam').exists():
            return False
        if obj is None:
            return True
        return obj.mosque.created_by_id == request.user.id

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'mosque' and not request.user.is_superuser:
            kwargs['queryset'] = Mosque.objects.filter(created_by=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

