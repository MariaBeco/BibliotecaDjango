# BibliotecaDjango

**2.1 Diseño antes de programar**
**Entidades:** Categoría, Autor, Libro, Ejemplar (copia física), Estudiante, Préstamo. 
**Campos:**
| Modelo | Campos |
|---|---|
| Categoria | nombre (único) |
| Autor | nombre |
| Libro | titulo, anio_publicacion, isbn (único), categoria, autores |
| Ejemplar | libro, codigo_inventario (único), condicion (nuevo/usado/dañado) |
| Estudiante | codigo (único), nombre, correo (único) |
| Prestamo | ejemplar, estudiante, fecha_prestamo, fecha_limite, fecha_devolucion (puede estar vacía) |

**Relaciones:**
| Par | Tipo | Dónde se escribe | on_delete y por qué |
|---|---|---|---|
| Categoría y Libro | 1 a muchos | `ForeignKey` en Libro | `PROTECT`: no dejar borrar una categoría que tiene libros |
| Libro y Autor | muchos a muchos | `ManyToManyField` en Libro | no aplica (Django crea la tabla intermedia `biblioteca_libro_autores`) |
| Libro y Ejemplar | 1 a muchos | `ForeignKey` en Ejemplar | `CASCADE`: si el libro desaparece del catálogo, sus copias no tienen sentido |
| Ejemplar y Préstamo | 1 a muchos | `ForeignKey` en Préstamo | `PROTECT`: no perder el historial de préstamos |
| Estudiante y Préstamo | 1 a muchos | `ForeignKey` en Préstamo | `PROTECT`: no se puede borrar un estudiante con historial |

**2.3 Preguntas guía para el diseño**
- **¿Por qué Libro y Ejemplar son modelos distintos?** Porque el título, ISBN y autores son del libro y se repiten igual en todas las copias. Si fuera un solo modelo, con 3 copias tendrías 3 filas con el mismo título e ISBN repetidos (y el ISBN ya no podría ser único). Además se presta la copia, no el libro.
- **¿Dónde va la fecha real de devolución?** En el Préstamo (`fecha_devolucion`). Mientras el libro sigue prestado vale **NULL** (vacío). Por eso lleva `null=True, blank=True`. "Préstamo activo" = préstamo con `fecha_devolucion` vacía.
- **¿Qué on_delete entre préstamo y estudiante?** `PROTECT`. Si fuera `CASCADE`, borrar un estudiante borraría su historial de préstamos y la biblioteca perdería el registro de quién tuvo qué libro.

**2.4 La regla de la copia prestada**
Elegimos una **restricción en la base de datos** (`UniqueConstraint` con condición): "solo puede haber un préstamo **sin fecha de devolución** por cada ejemplar".
la base de datos la hace cumplir siempre, sin importar si el préstamo se guarda desde el admin, desde el shell con `.save()` o desde un script. Con `clean()` la regla se salta si alguien guarda con `.save()` sin llamar `full_clean()`. Además, desde Django 4.1 el admin también valida las constraints, así que la bibliotecaria ve un mensaje claro en el formulario en vez de un error feo.