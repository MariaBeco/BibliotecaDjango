from django.contrib import admin
from .models import Autor, Categoria, Libro, Ejemplar, Estudiante, Prestamo
from datetime import date

# Register your models here.
admin.site.register(Categoria)

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("codigo","nombre")
    search_fields = ("codigo","nombre")

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)

class EjemplarInline(admin.TabularInline):
    model = Ejemplar
    extra = 1

@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display=("titulo","isbn","categoria", "anio_publicacion")
    search_fields=("titulo","autores__nombre","isbn")
    list_filter=("categoria","autores__nombre","anio_publicacion")
    inlines=[EjemplarInline]

@admin.register(Ejemplar)
class EjemplarAdmin(admin.ModelAdmin):
    list_display=("codigo_inventario","libro","condicion")
    search_fields=("codigo_inventario","libro__titulo")
    list_filter=("condicion","libro__categoria")

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display=("ejemplar", "estudiante", "fecha_prestamo", "fecha_limite", "devuelto")
    search_fields=("estudiante__codigo", "estudiante__nombre", "ejemplar__codigo_inventario", "ejemplar__libro__titulo")
    list_filter=("fecha_devolucion", "fecha_prestamo")
    autocomplete_fields=("ejemplar", "estudiante")
    readonly_fields=("devuelto",)
    actions=["marcar_devueltos"]

    @admin.display(boolean=True, description="Devuelto")
    def devuelto(self, obj):
        return obj.fecha_devolucion is not None

    @admin.action(description="Marcar como devueltos (con la fecha de hoy)")
    def marcar_devueltos(self, request, queryset):
        queryset.filter(fecha_devolucion__isnull=True).update(fecha_devolucion=date.today())

