"""
Carga datos de prueba para los retos de la fase 5 y 6.

Uso:
    python manage.py cargar_datos

Se puede ejecutar varias veces: no duplica registros (usa get_or_create).
Los datos están pensados para que cada reto tenga una respuesta interesante:
  - GGM tiene 2 libros y "The Pragmatic Programmer" tiene 2 autores.
  - "Cien años de soledad" es el libro más prestado (3 préstamos).
  - Carlos Díaz nunca ha pedido un préstamo.
  - María Rojas tiene 2 préstamos activos (para ver el efecto de distinct()).
  - Hay préstamos devueltos, activos y uno vencido.
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from biblioteca.models import (
    Autor, Categoria, Libro, Ejemplar, Estudiante, Prestamo,
)


class Command(BaseCommand):
    help = "Carga datos de prueba (autores, libros, copias, estudiantes y préstamos)."

    @transaction.atomic
    def handle(self, *args, **options):
        # --- Categorías ---
        novela, _ = Categoria.objects.get_or_create(nombre="Novela")
        ingenieria, _ = Categoria.objects.get_or_create(nombre="Ingeniería")

        # --- Autores ---
        gabo, _ = Autor.objects.get_or_create(nombre="Gabriel García Márquez")
        martin, _ = Autor.objects.get_or_create(nombre="Robert C. Martin")
        hunt, _ = Autor.objects.get_or_create(nombre="Andrew Hunt")
        thomas, _ = Autor.objects.get_or_create(nombre="David Thomas")

        # --- Libros (el ISBN es la clave única; los ISBN son de ejemplo) ---
        def crear_libro(isbn, titulo, anio, categoria, idioma, autores):
            libro, _ = Libro.objects.get_or_create(
                isbn=isbn,
                defaults={
                    "titulo": titulo,
                    "anio_publicacion": anio,
                    "categoria": categoria,
                    "idioma": idioma,
                },
            )
            libro.autores.add(*autores)  # add() no duplica si ya existe
            return libro

        cien = crear_libro("9780060883287", "Cien años de soledad", 1967, novela, "Español", [gabo])
        cronica = crear_libro("9781400034956", "Crónica de una muerte anunciada", 1981, novela, "Español", [gabo])
        clean_code = crear_libro("9780132350884", "Clean Code", 2008, ingenieria, "Inglés", [martin])
        clean_arch = crear_libro("9780134494166", "Clean Architecture", 2017, ingenieria, "Inglés", [martin])
        pragmatic = crear_libro("9780201616224", "The Pragmatic Programmer", 1999, ingenieria, "Inglés", [hunt, thomas])

        # --- Ejemplares (copias físicas), 8 en total ---
        def crear_ejemplar(codigo, libro, condicion):
            ejemplar, _ = Ejemplar.objects.get_or_create(
                codigo_inventario=codigo,
                defaults={"libro": libro, "condicion": condicion},
            )
            return ejemplar

        cien_1 = crear_ejemplar("CIEN-001", cien, "use")
        cien_2 = crear_ejemplar("CIEN-002", cien, "new")
        cron_1 = crear_ejemplar("CRON-001", cronica, "use")
        clean_1 = crear_ejemplar("CLEAN-001", clean_code, "new")
        clean_2 = crear_ejemplar("CLEAN-002", clean_code, "dam")
        arq_1 = crear_ejemplar("ARQ-001", clean_arch, "new")
        prag_1 = crear_ejemplar("PRAG-001", pragmatic, "use")
        prag_2 = crear_ejemplar("PRAG-002", pragmatic, "new")

        # --- Estudiantes (el código tiene máximo 7 caracteres) ---
        def crear_estudiante(codigo, nombre, correo):
            estudiante, _ = Estudiante.objects.get_or_create(
                codigo=codigo,
                defaults={"nombre": nombre, "correo": correo},
            )
            return estudiante

        ana = crear_estudiante("1152001", "Ana Pérez", "anaperez@ufps.edu.co")
        luis = crear_estudiante("1152002", "Luis Gómez", "luisgomez@ufps.edu.co")
        maria = crear_estudiante("1152003", "María Rojas", "mariarojas@ufps.edu.co")
        crear_estudiante("1152004", "Carlos Díaz", "carlosdiaz@ufps.edu.co")  # nunca pide préstamos

        # --- Préstamos: 7 en total (3 devueltos y 4 activos) ---
        def crear_prestamo(ejemplar, estudiante, salida, limite, devolucion=None):
            Prestamo.objects.get_or_create(
                ejemplar=ejemplar,
                estudiante=estudiante,
                fecha_prestamo=salida,
                defaults={"fecha_limite": limite, "fecha_devolucion": devolucion},
            )

        # Devueltos
        crear_prestamo(cien_1, ana, date(2026, 10, 1), date(2026, 10, 15), date(2026, 10, 12))
        crear_prestamo(clean_2, luis, date(2026, 10, 5), date(2026, 10, 19), date(2026, 10, 17))
        crear_prestamo(prag_1, maria, date(2026, 9, 20), date(2026, 10, 4), date(2026, 10, 2))
        # Activos (sin fecha de devolución)
        crear_prestamo(cien_1, luis, date(2026, 11, 5), date(2026, 11, 19))   # vencido
        crear_prestamo(clean_1, ana, date(2026, 11, 15), date(2026, 11, 29))
        crear_prestamo(prag_1, maria, date(2026, 11, 17), date(2026, 12, 1))
        crear_prestamo(cien_2, maria, date(2026, 11, 18), date(2026, 12, 2))

        self.stdout.write(self.style.SUCCESS("Datos de prueba cargados."))
        self.stdout.write(
            f"Autores: {Autor.objects.count()} | Categorías: {Categoria.objects.count()} | "
            f"Libros: {Libro.objects.count()} | Ejemplares: {Ejemplar.objects.count()} | "
            f"Estudiantes: {Estudiante.objects.count()} | Préstamos: {Prestamo.objects.count()} "
            f"(activos: {Prestamo.objects.filter(fecha_devolucion__isnull=True).count()})"
        )
