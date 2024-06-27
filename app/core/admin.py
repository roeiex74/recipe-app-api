"""
Django admin customizaion.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core import models
from django.utils.translation import gettext_lazy as _


# Register your models here.
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "name"]
    ordering = ["id"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser")},
        ),
        (_("Dates"), {"fields": ("last_login",)}),
    )
    readonly_fields = ["last_login"]

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "name",
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Recipe)
