from django.contrib import admin
from .models import *

# Register your models here.


admin.site.register(Candidate)
admin.site.register(Club)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
