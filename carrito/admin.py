from django.contrib import admin
from .models import Producto, Orden, OrdenItem


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock", "creado")
    list_editable = ("precio", "stock")
    prepopulated_fields = {"slug": ("nombre",)}
    search_fields = ("nombre",)
    ordering = ("nombre",)


class OrdenItemInline(admin.TabularInline):
    model = OrdenItem
    extra = 0
    readonly_fields = ("precio",)


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "estado", "total", "creado")
    list_filter = ("estado", "creado")
    inlines = [OrdenItemInline]
    readonly_fields = ("total", "creado", "estado")
    date_hierarchy = "creado"
    search_fields = ("usuario__username",)
    ordering = ("-creado",)


@admin.register(OrdenItem)
class OrdenItemAdmin(admin.ModelAdmin):
    list_display = ("orden", "producto", "cantidad", "precio")
    list_filter = ("orden",)
    search_fields = ("producto__nombre",)
