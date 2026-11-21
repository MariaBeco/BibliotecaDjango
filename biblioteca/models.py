from django.db import models
from django.db.models import Q

# Create your models here.

class Autor(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Libro(models.Model):
    titulo= models.CharField(max_length=100)
    anio_publicacion= models.PositiveIntegerField()
    isbn= models.CharField(unique=True, max_length=13)
    autores= models.ManyToManyField(Autor)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.titulo} ({self.anio_publicacion})"
    

class Ejemplar(models.Model):
    libro= models.ForeignKey(Libro, on_delete=models.CASCADE)
    codigo_inventario= models.CharField(max_length=100, unique=True)
    condicion= models.CharField(max_length=3, choices=[("new", "Nuevo"),("use", "Usado"),("dam","Dañado")])

    def __str__(self):
        return f"{self.libro.titulo} - {self.codigo_inventario} - {self.get_condicion_display()}"

class Estudiante(models.Model):
    codigo= models.CharField(max_length=7, unique=True)
    nombre= models.CharField(max_length=150)
    correo = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre} - {self.correo}"

class Prestamo(models.Model):
    ejemplar= models.ForeignKey(Ejemplar, on_delete=models.PROTECT)
    estudiante= models.ForeignKey(Estudiante, on_delete=models.PROTECT)
    fecha_prestamo= models.DateField()
    fecha_limite= models.DateField()
    fecha_devolucion= models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ejemplar"],
                condition=Q(fecha_devolucion__isnull=True),
                name="una_copia_un_prestamo_activo",
            ),
        ]

    def __str__(self):
        estado = "devuelto" if self.fecha_devolucion else "activo"
        return f"copia:{self.ejemplar.codigo_inventario} - estudiante:{self.estudiante.codigo} - ({estado})"
