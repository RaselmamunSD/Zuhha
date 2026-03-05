from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db.models import Q
from unfold.admin import ModelAdmin
from .models import ImamUser


class ImamUserCreationForm(forms.ModelForm):
	password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
	password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

	class Meta:
		model = ImamUser
		fields = ["username", "first_name", "last_name", "email", "is_active"]

	def clean(self):
		cleaned_data = super().clean()
		if cleaned_data.get("password1") != cleaned_data.get("password2"):
			raise ValidationError("Passwords do not match.")
		return cleaned_data

	def clean_username(self):
		username = (self.cleaned_data.get("username") or "").strip()
		if User.objects.filter(username__iexact=username).exists():
			raise ValidationError("This username already exists.")
		return username

	def save(self, commit=True):
		user = ImamUser(
			username=self.cleaned_data["username"],
			first_name=self.cleaned_data.get("first_name", ""),
			last_name=self.cleaned_data.get("last_name", ""),
			email=self.cleaned_data.get("email", ""),
			is_active=self.cleaned_data.get("is_active", True),
			is_staff=True,  # Enable Django admin access for Imam
		)
		user.set_password(self.cleaned_data["password1"])
		if commit:
			user.save()
			imam_group, _ = Group.objects.get_or_create(name="Imam")
			user.groups.add(imam_group)
			# Grant mosque and monthly timetable permissions to Imam
			from django.contrib.contenttypes.models import ContentType
			from django.contrib.auth.models import Permission
			from find_mosque.models import Mosque, MosqueMonthlyPrayerTime
			mosque_ct = ContentType.objects.get_for_model(Mosque)
			monthly_ct = ContentType.objects.get_for_model(MosqueMonthlyPrayerTime)
			permissions = Permission.objects.filter(
				Q(content_type=mosque_ct, codename__in=['view_mosque', 'change_mosque']) |
				Q(content_type=monthly_ct, codename__in=['view_mosquemonthlyprayertime', 'add_mosquemonthlyprayertime', 'change_mosquemonthlyprayertime', 'delete_mosquemonthlyprayertime'])
			)
			imam_group.permissions.add(*permissions)
		return user

	def save_m2m(self):
		"""Handle M2M relations. Groups are assigned in save_model, so this is a no-op."""
		pass


@admin.register(ImamUser)
class ImamUserAdmin(ModelAdmin):
	add_form = ImamUserCreationForm
	list_display = ["username", "first_name", "last_name", "email", "is_active", "last_login"]
	list_filter = ["is_active", "is_staff", "is_superuser"]
	search_fields = ["username", "first_name", "last_name", "email"]
	ordering = ["username"]
	readonly_fields = ["last_login", "date_joined"]

	fieldsets = (
		("Imam Account", {"fields": ("username", "password")}),
		("Personal Info", {"fields": ("first_name", "last_name", "email")}),
		("Status", {"fields": ("is_active",)}),
		("Important dates", {"fields": ("last_login", "date_joined")}),
	)

	add_fieldsets = (
		(
			None,
			{
				"classes": ("wide",),
				"fields": ("username", "first_name", "last_name", "email", "is_active", "password1", "password2"),
			},
		),
	)

	def get_form(self, request, obj=None, **kwargs):
		defaults = {}
		if obj is None:
			defaults["form"] = self.add_form
		defaults.update(kwargs)
		return super().get_form(request, obj, **defaults)

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		
		# Ensure the Imam group is assigned
		imam_group, _ = Group.objects.get_or_create(name="Imam")
		obj.groups.add(imam_group)
	
	def has_module_permission(self, request):
		"""Only superusers can manage Imam users."""
		return request.user.is_superuser
