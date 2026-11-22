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

**Lectura del SQL de la migración inicial**

**3.2:** 
Revisamos el SQL con `python manage.py sqlmigrate biblioteca 0001`.

- **Nombres de las tablas:** Django nombra cada tabla como `nombreapp_nombremodelo`, en minúscula. Por ejemplo, el modelo `Prestamo` se convierte en la tabla `biblioteca_prestamo`.
- **Tabla intermedia del muchos a muchos:** aparece como `biblioteca_libro_autores`, aunque no escribimos ningún modelo para ella. Django la crea a partir del `ManyToManyField` de `Libro`, porque una sola columna no puede guardar una lista de autores. Tiene dos columnas, `libro_id` y `autor_id`, y cada fila representa un par "este libro fue escrito por este autor".
- **Llaves foráneas:** cada `ForeignKey` se convierte en una columna con el nombre del campo más `_id`. Por ejemplo, `categoria` queda como `categoria_id`, que guarda el id de la categoría. El `REFERENCES "biblioteca_categoria"` indica que ese valor debe corresponder a una categoría existente.
- **Campos opcionales:** `fecha_devolucion` aparece como `date NULL` (puede quedar vacía) porque la definimos con `null=True`, mientras que `fecha_limite` aparece como `NOT NULL` (obligatoria).
- **Regla de la copia prestada:** aparece como `CREATE UNIQUE INDEX "una_copia_un_prestamo_activo" ... WHERE "fecha_devolucion" IS NULL`. 
- **WHERE** hace que la regla solo se aplique a los préstamos cuya fecha de devolución está vacía, es decir, a los préstamos activos. Así, una copia no puede tener dos préstamos activos al mismo tiempo, pero sí puede volver a prestarse después de ser devuelta.

**3.4:**
- la migración es la 0002, la operación es AddField (agregar un campo a libro), Django preguntó por un valor por defecto porque ya había libros sin idioma, elegiste la opción 1 con "Español", y preserve_default=False hace que ese valor solo se use para los libros existentes.

## 7. Consultas del ORM

<!-- sara aca va lo suyo no se le olvide si se le olvida que problemota en el que nos metemos pq imaginese esto saliendo en el readme no muy duro que tremendo problema seria ese -->

### Reto 6. Préstamos por estudiante, contando los ya devueltos

**Código**
```python
from django.db.models import Count
[(e.nombre, e.total) for e in Estudiante.objects.annotate(total=Count("prestamo"))]
```

**Predicción**
Espero que a cada objeto Estudiante se le agregue una columna calculada llamada total, y que la función Count cuente cuántos préstamos tiene cada estudiante. Funciona como un GROUP BY por estudiante, cada uno aparece una sola vez con su cantidad. Como no filtramos por fecha de devolución, cuenta los devueltos y los activos, y Carlos, que no tiene préstamos, queda con 0.

**Resultado**
```
[('Ana Pérez', 2), ('Luis Gómez', 2), ('María Rojas', 3), ('Carlos Díaz', 0)]
```

---

### Reto 7. El libro más prestado

**Código**
```python
l = Libro.objects.annotate(total=Count("ejemplar__prestamo")).order_by("-total").first()
print(l, l.total)
```

**Predicción**
Espero que a cada objeto Libro se le agregue una columna calculada llamada total, y que la función Count cuente cuántos préstamos tiene cada libro, pasando primero por sus copias y luego por los préstamos de cada copia. Después se ordena de mayor a menor y se toma el primero. Espero que salga Cien años de soledad con 3 préstamos, porque entre sus dos copias suma más préstamos que cualquier otro libro. Cuenta los devueltos y los activos, y los libros sin préstamos quedan con 0.

**Resultado**
```
Cien años de soledad (1967) 3
```

---

### Reto 8. Estudiantes que nunca han pedido un préstamo

**Código**
```python
Estudiante.objects.filter(prestamo__isnull=True)
```

**Predicción**
Espero que devuelva solo a Carlos Díaz, porque es el único estudiante que no tiene ningún préstamo registrado. El filtro busca los estudiantes cuya relación con préstamo está vacía, así que los que tienen al menos un préstamo, activo o devuelto, no aparecen.

**Resultado**
```
<QuerySet [<Estudiante: 1152004 - Carlos Díaz - carlosdiaz@ufps.edu.co>]>
```

---

### Reto 9. Marcar un préstamo como devuelto

**Código**
```python
from datetime import date
p = Prestamo.objects.filter(fecha_devolucion__isnull=True).first()
print(p.fecha_devolucion)
p.fecha_devolucion = date.today()
p.save()
Prestamo.objects.get(id=p.id).fecha_devolucion
```

**Predicción**
Espero que antes del cambio la fecha de devolución sea None, porque el préstamo está activo, y que después de asignar la fecha de hoy y guardar con save, al leerlo de nuevo desde la base de datos aparezca la fecha de hoy. Volver a leerlo con get confirma que el cambio quedó guardado y no solo en memoria.

**Resultado**
```
None
datetime.date(2026, 11, 22)
```

---

### Reto 10. Borrar un autor y ver qué pasa con sus libros

**Código**
```python
autor.libro_set.all()
Libro.objects.count()
autor.delete()
Libro.objects.count()
list(libro.autores.all())
```

**Predicción**
Espero que al borrar el autor la cantidad de libros siga igual, y que el libro quede con la lista de autores vacía. La relación entre libro y autor es de muchos a muchos, así que solo se borra el enlace en la tabla intermedia y los libros no se eliminan. El on_delete no aplica aquí, porque solo existe en las relaciones de tipo ForeignKey.

**Resultado**
```
<QuerySet [<Libro: Libro de prueba (2020)>]>
6
6
[]
```
