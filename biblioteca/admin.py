from django.contrib import admin
from .models import Autor, Categoria, Libro, Ejemplar, Estudiante, Prestamo

# Register your models here.
admin.site.register(Autor)
admin.site.register(Categoria)
admin.site.register(Libro)
admin.site.register(Estudiante)
admin.site.register(Ejemplar)
admin.site.register(Prestamo)
