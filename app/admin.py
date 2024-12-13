from django.contrib import admin
from app.models import *

admin.site.site_header = 'MSWD Management Application'
admin.site.site_title = 'MSWD Management Application'

class BenediciaryAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'middle_name', 'last_name', 'birth_date','contact_number')
    list_filter = ('first_name', 'last_name')

class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'middle_name', 'last_name', 'contact_number', 'marital_status')
    list_filter = ('contact_number', 'marital_status')
    list_editable = ('contact_number', 'marital_status')

class AssistanceAdmin(admin.ModelAdmin):
    list_display = ('assistance_type','is_notified','is_claimed', 'date_provided')
    list_editable = ('is_notified','is_claimed', 'date_provided')

admin.site.register(Assistance, AssistanceAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Beneficiary, BenediciaryAdmin)
admin.site.register(NotificationSetting)