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

# Fase 7: EL DIAGRAMA DE RELACIONES CON MERMAID

erDiagram
    CATEGORIA ||--o{ LIBRO : "clasifica"
    LIBRO }o--|{ AUTOR : "escrito por"
    LIBRO ||--o{ EJEMPLAR : "tiene"
    EJEMPLAR ||--o{ PRESTAMO : "se presta en"
    ESTUDIANTE ||--o{ PRESTAMO : "realiza"

    AUTOR {
        int id PK
        string nombre
    }
    CATEGORIA {
        int id PK
        string nombre UK
    }
    LIBRO {
        int id PK
        string titulo
        int anio_publicacion
        string isbn UK
        string idioma
        int categoria_id FK
    }
    EJEMPLAR {
        int id PK
        int libro_id FK
        string codigo_inventario UK
        string condicion "new, use o dam"
    }
    ESTUDIANTE {
        int id PK
        string codigo UK
        string nombre
        string correo UK
    }
    PRESTAMO {
        int id PK
        int ejemplar_id FK
        int estudiante_id FK
        date fecha_prestamo
        date fecha_limite
        date fecha_devolucion "opcional, NULL si no se ha devuelto"
    }
    
### Correcciones al diagrama generado por IA

El diagrama se generó con Claude a partir de nuestro `models.py` y luego lo revisamos línea por línea contra el código.

**Corrección: cardinalidad entre Libro y Autor**

- **Lo que generó el agente:** `LIBRO }o--o{ AUTOR` (cero o muchos en ambos lados).
- **Lo que corregimos:** `LIBRO }o--|{ AUTOR`.
- **Por qué:** el campo `autores = models.ManyToManyField(Autor)` no tiene `blank=True`, así que el panel de administración no permite guardar un libro sin al menos un autor. Por eso, del lado del autor la cardinalidad es "uno o muchos". Del lado del libro se mantiene "cero o muchos", porque un autor tiene que existir antes de poder asignarlo a un libro, así que puede estar registrado sin libros.
- **Matiz:** esta regla la hace cumplir el formulario del admin, no la base de datos. Desde el shell sí es posible crear un libro sin autores.

**Verificación: tipo de los `id` y llaves foráneas**

Dudamos de que los `id` y las llaves foráneas aparecieran como `int`, porque nuestros códigos (`codigo`, `codigo_inventario`, `isbn`) son texto. Lo verificamos con `python manage.py sqlmigrate biblioteca 0001`: Django crea el `id` de cada tabla como un entero autoincremental, y las llaves foráneas (`categoria_id`, `libro_id`, `ejemplar_id`, `estudiante_id`) guardan ese número, no el código. El diagrama era correcto en este punto.

**Otros puntos revisados sin cambios**

- Están los 6 modelos y no hay modelos ni campos inventados.
- Cada `ForeignKey` aparece como uno a muchos, con el "uno" en el modelo al que apunta la llave.
- `fecha_devolucion` aparece como opcional, porque tiene `null=True`.