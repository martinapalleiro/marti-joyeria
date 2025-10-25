from django.contrib import admin
from .models import Producto, Orden, OrdenItem

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock")
    prepopulated_fields = {"slug": ("nombre",)}

admin.site.register(Orden)
admin.site.register(OrdenItem)