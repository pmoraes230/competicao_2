from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Cliente)
admin.site.register(models.Evento)
admin.site.register(models.Perfil)
admin.site.register(models.Setorevento)
admin.site.register(models.Usuario)
admin.site.register(models.Venda)