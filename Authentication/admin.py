from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

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
		)
		user.set_password(self.cleaned_data["password1"])
		if commit:
			user.save()
			imam_group, _ = Group.objects.get_or_create(name="Imam")
			user.groups.add(imam_group)
		return user


@admin.register(ImamUser)
class ImamUserAdmin(admin.ModelAdmin):
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
