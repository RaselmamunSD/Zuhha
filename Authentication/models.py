from django.contrib.auth.models import User, UserManager
from django.db import models


class ImamUserManager(UserManager):
	"""
	Custom manager for Imam users.
	Filters to only show users in the Imam group.
	"""
	def get_queryset(self):
		return (
			super()
			.get_queryset()
			.filter(groups__name="Imam")
			.distinct()
		)


class ImamUser(User):
	"""
	Proxy model for users assigned to the Imam group.
	"""

	objects = ImamUserManager()

	class Meta:
		proxy = True
		verbose_name = "Imam User"
		verbose_name_plural = "Imam Users"
