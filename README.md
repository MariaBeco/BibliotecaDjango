# Biblioteca Django

Es una herramienta qué permitirá organizar los préstamos de la biblioteca de una universidad, permite: registrar libros, copias, estudiantes y préstamos, y manejarlos desde el panel de administración.

## 2. Tecnologías 

- **Versión de Python:** Python 3.15.2
- **Versión de Django:** 6.1.3
- **Base de datos:** SQLite (la que trae Django por defecto). El archivo ```db.sqlite3``` no se sube al repositorio: se crea al ejecutar ```python manage.py migrate```
- **Versión de SQLite:** 3.53.4

## 3. Instalación y ejecución

Requisitos previos: tener instalados [Python](https://www.python.org/downloads/) y [Git](https://git-scm.com/).

1. **Clonar el repositorio y entrar a la carpeta:**
   ```bash
   git clone https://github.com/MariaBeco/BibliotecaDjango.git
   cd BibliotecaDjango
   ```

2. **Crear y activar el entorno virtual.** Así las librerías del proyecto quedan aisladas de las del resto del computador.
   ```bash
   python -m venv venv
   ```
   - Windows (PowerShell): `.\venv\Scripts\activate`
   - Linux / macOS: `source venv/bin/activate`

   Sabrás que está activo porque la terminal empieza con `(venv)`.

3. **Instalar las dependencias** (Django y lo que necesita):
   ```bash
   pip install -r requirements.txt
   ```

4. **Crear la base de datos.** Aplica las migraciones y crea el archivo `db.sqlite3` con todas las tablas:
   ```bash
   python manage.py migrate
   ```

5. **Crear un usuario administrador** para entrar al panel. Pide usuario, correo (opcional) y contraseña:
   ```bash
   python manage.py createsuperuser
   ```

6. **Arrancar el servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```

7. **Abrir en el navegador** http://127.0.0.1:8000/admin/ e ingresar con el usuario del paso 5.

Para detener el servidor, presiona `Ctrl + C` en la terminal.

## 4. Estructura del proyecto

```
BibliotecaDjango/
├── config/                  # configuración general del proyecto
│   ├── settings.py          # lista de apps instaladas y base de datos que utiliza
│   └── urls.py              # directorio de páginas
├── biblioteca/              # app con la lógica de la biblioteca
│   ├── models.py            # modelos de la app
│   ├── admin.py             # configuración del panel de administración (/admin)
│   ├── migrations/          # archivos que generó django con makemigrations, es el historial de cambios de la base de datos
│   └── management/commands/
│       └── cargar_datos.py  # llena la base de datos con datos de prueba
├── manage.py                # administrador del proyecto
├── requirements.txt         # versiones de asgiref, Django, sqlparse, tzdata
├── .gitignore               # archivos que no deben subirse a GitHub
└── README.md                # Aquí estas :D
```
Los demás archivos los genera Django automáticamente.

## 5. Modelo de datos

### DIAGRAMA DE RELACIONES

```mermaid
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
```

**Entidades:** Categoría, Autor, Libro, Ejemplar (copia física), Estudiante, Préstamo. 
**Campos:**
| Modelo | Campos |
|---|---|
| Categoria | nombre (único) |
| Autor | nombre |
| Libro | titulo, anio_publicacion, isbn (único), categoria, autores, idioma |
| Ejemplar | libro, codigo_inventario (único), condicion (nuevo/usado/dañado) |
| Estudiante | codigo (único), nombre, correo (único) |
| Prestamo | ejemplar, estudiante, fecha_prestamo, fecha_limite, fecha_devolucion (puede estar vacía) |

### Relaciones:
| Par | Tipo | Dónde se escribe | on_delete y por qué |
|---|---|---|---|
| Categoría y Libro | 1 a muchos | `ForeignKey` en Libro | `PROTECT`: no dejar borrar una categoría que tiene libros |
| Libro y Autor | muchos a muchos | `ManyToManyField` en Libro | no aplica (Django crea la tabla intermedia `biblioteca_libro_autores`) |
| Libro y Ejemplar | 1 a muchos | `ForeignKey` en Ejemplar | `CASCADE`: si el libro desaparece del catálogo, sus copias no tienen sentido |
| Ejemplar y Préstamo | 1 a muchos | `ForeignKey` en Préstamo | `PROTECT`: no perder el historial de préstamos |
| Estudiante y Préstamo | 1 a muchos | `ForeignKey` en Préstamo | `PROTECT`: no se puede borrar un estudiante con historial |

### Relaciones explicadas
- Una categoría agrupa muchos libros y cada libro pertenece a una sola categoría.
- Un libro está escrito al menos por un autor y un autor puede tener ninguno o varios libros registrados.
- Un libro tiene cero o muchos ejemplares y cada ejemplar pertenece a un libro.
- Un ejemplar puede estar en uno o muchos préstamos y cada préstamo debe tener un ejemplar, pero un ejemplar solo puede tener un préstamo activo a la vez.
- Un estudiante puede realizar uno o muchos préstamos y cada préstamo debe tener un estudiante.

### Decisiones de diseño
- **Libro y Ejemplar son modelos distintos** porque el título, ISBN y autores son del libro y se repiten igual en todas las copias. Si fuera un solo modelo, con 3 copias tendrías 3 filas con el mismo título e ISBN repetidos (y el ISBN ya no podría ser único). Además se presta la copia, no el libro.
- **La fecha real de devolución se guarda en el Préstamo** (`fecha_devolucion`). Mientras el libro sigue prestado, el campo queda vacío (NULL); por eso lleva `null=True, blank=True`. Un préstamo con este campo vacío es un **préstamo activo**.
- **Entre Préstamo y Estudiante usamos `on_delete=PROTECT`**, que impide borrar un estudiante que tenga préstamos. Con `CASCADE`, borrar un estudiante borraría también su historial y la biblioteca perdería el registro de quién tuvo cada libro.

### La regla de la copia prestada
Elegimos una **restricción en la base de datos** (`UniqueConstraint` con condición): "solo puede haber un préstamo **sin fecha de devolución** por cada ejemplar".
La base de datos la hace cumplir siempre, sin importar si el préstamo se guarda desde el admin, desde el shell con `.save()` o desde un script. Con `clean()` la regla se salta si alguien guarda con `.save()` sin llamar `full_clean()`. Además, desde Django 4.1 el admin también valida las constraints, así que la bibliotecaria ve un mensaje claro en el formulario en vez de un error feo.

**Al probar la restricción**

Para probar la restricción se hizo a través de shell de Django. Primero se obtuvieron los datos que necesitábamos de la base de datos, la copia CIEN-001 y a la estudiante Ana:
```python
from biblioteca.models import Ejemplar, Estudiante, Prestamo
from datetime import date
copia = Ejemplar.objects.get(codigo_inventario="CIEN-001")
ana = Estudiante.objects.get(codigo="1152001")
```

Al querer crear un nuevo préstamo con la copia que ya se encontraba en otro préstamo activo:
```python
Prestamo.objects.create(ejemplar=copia, estudiante=ana, fecha_prestamo=date.today(), fecha_limite=date(2026, 12, 6))
```
la base de datos lanzó el siguiente error:
```
sqlite3.IntegrityError: UNIQUE constraint failed: biblioteca_prestamo.ejemplar_id
```

Este error prueba que la regla funciona y la base de datos no guardó el préstamo. Para finalizar, se le asignó la fecha de hoy como la fecha de devolución del préstamo que tenía la copia de la prueba:
```python
p = Prestamo.objects.get(ejemplar=copia, fecha_devolucion__isnull=True)
p.fecha_devolucion = date.today()
p.save()
```
y de nuevo, se probó crear el préstamo con esa copia para la estudiante Ana, el cual se realizó exitosamente mostrando:
```
<Prestamo: copia:CIEN-001 - estudiante:1152001 - (activo)>
```

### Lectura del SQL de la migración inicial

Revisamos el SQL con `python manage.py sqlmigrate biblioteca 0001`.

- **Nombres de las tablas:** Django nombra cada tabla como `nombreapp_nombremodelo`, en minúscula. Por ejemplo, el modelo `Prestamo` se convierte en la tabla `biblioteca_prestamo`.
- **Tabla intermedia del muchos a muchos:** aparece como `biblioteca_libro_autores`, aunque no escribimos ningún modelo para ella. Django la crea a partir del `ManyToManyField` de `Libro`, porque una sola columna no puede guardar una lista de autores. Tiene dos columnas, `libro_id` y `autor_id`, y cada fila representa un par "este libro fue escrito por este autor".
- **Llaves foráneas:** cada `ForeignKey` se convierte en una columna con el nombre del campo más `_id`. Por ejemplo, `categoria` queda como `categoria_id`, que guarda el id de la categoría. El `REFERENCES "biblioteca_categoria"` indica que ese valor debe corresponder a una categoría existente.
- **Campos opcionales:** `fecha_devolucion` aparece como `date NULL` (puede quedar vacía) porque la definimos con `null=True`, mientras que `fecha_limite` aparece como `NOT NULL` (obligatoria).
- **Regla de la copia prestada:** aparece como `CREATE UNIQUE INDEX "una_copia_un_prestamo_activo" ... WHERE "fecha_devolucion" IS NULL`. 
- **WHERE** hace que la regla solo se aplique a los préstamos cuya fecha de devolución está vacía, es decir, a los préstamos activos. Así, una copia no puede tener dos préstamos activos al mismo tiempo, pero sí puede volver a prestarse después de ser devuelta.

### Ejercicio: agregar un campo nuevo

### Ejercicio: agregar un campo nuevo

Para practicar una segunda migración, agregamos al modelo `Libro` el campo obligatorio `idioma`:

```python
idioma = models.CharField(max_length=25)
```

Al ejecutar `python manage.py makemigrations`, Django mostró este mensaje:

```
It is impossible to add a non-nullable field 'idioma' to libro without specifying a default.
This is because the database needs something to populate existing rows.
Please select a fix:
 1) Provide a one-off default now (will be set on all existing rows with a null value for this column)
 2) Quit and manually define a default value in models.py.
```

Django pregunta esto porque el campo no admite valores vacíos y en la base de datos ya había libros guardados sin idioma, así que necesita saber con qué rellenarlos. Elegimos la opción 1 e indicamos `"Español"` como valor.

Se generó la migración `0002_libro_idioma.py`, que contiene una operación `AddField` (agregar un campo al modelo `libro`) con `preserve_default=False`. Esto significa que el valor `"Español"` se usa una sola vez, para rellenar los libros que ya existían; los libros nuevos deben indicar su idioma obligatoriamente. Finalmente, aplicamos la migración con `python manage.py migrate`.

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

Primero se crea un autor de prueba con un libro, para no borrar datos reales:
```python
autor, _ = Autor.objects.get_or_create(nombre="Autor Prueba")
libro, _ = Libro.objects.get_or_create(isbn="9780000000001", defaults=dict(titulo="Libro de prueba", anio_publicacion=2020, categoria=Categoria.objects.first(), idioma="Español"))
libro.autores.add(autor)
```
Luego se borra el autor y se revisa qué pasó con el libro:
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

## 8. Optimización de consultas (problema N+1)

Para contar cuántas consultas ejecuta cada bloque se usó `CaptureQueriesContext`.

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext
from biblioteca.models import *
```

### 1. Predicción y medición del código con el problema

```python
with CaptureQueriesContext(connection) as ctx:
    for p in Prestamo.objects.all():
        print(p.estudiante.nombre, p.ejemplar.libro.titulo)

print(len(ctx), "consultas")
```

**Predicción:** Viendo el código, lo primero que se ve es que Prestamo objects all trae los 7 préstamos con una sola consulta. Luego el for pasa por cada préstamo, y en cada vuelta se usan tres cosas que no vienen en la tabla de préstamos, el estudiante, la copia y el libro de esa copia. Como Django no las trae por adelantado, cada vez que el código las toca tiene que ir a la base de datos a buscarlas. Entonces en cada vuelta hay 3 consultas, y como el for da 7 vueltas, son 21 consultas. Sumando la primera que trajo los préstamos, da 22.

**Resultado medido:** 22 consultas.

### 2. Corrección con select_related

```python
with CaptureQueriesContext(connection) as ctx:
    for p in Prestamo.objects.select_related("estudiante", "ejemplar__libro"):
        print(p.estudiante.nombre, p.ejemplar.libro.titulo)

print(len(ctx), "consultas")
```

**Resultado medido:** 1 consulta.

**Explicación:** Al agregar select_related con estudiante y ejemplar__libro, el número bajó de 22 a 1. Lo que cambió es que Django ya no espera a que el for pida cada dato, sino que desde el principio une las tablas de préstamo, estudiante, copia y libro y trae todo junto en una sola consulta. Cuando el for pide el nombre del estudiante o el título del libro, el dato ya está en memoria y no hay que volver a preguntarle a la base de datos.

### 3. Segundo caso: cada libro con la lista de sus autores

Código con el problema:

```python
with CaptureQueriesContext(connection) as ctx:
    for l in Libro.objects.all():
        print(l.titulo, [a.nombre for a in l.autores.all()])

print(len(ctx), "consultas")
```

**Resultado medido antes:** 7 consultas.

**Explicación del problema:** En el segundo caso, mostrar cada libro con sus autores, el código con el problema hizo 7 consultas con los 6 libros. Una trae los libros y después, por cada libro, el for pide sus autores y eso dispara otra consulta, o sea 1 más 6.

Corrección con prefetch_related:

```python
with CaptureQueriesContext(connection) as ctx:
    for l in Libro.objects.prefetch_related("autores"):
        print(l.titulo, [a.nombre for a in l.autores.all()])

print(len(ctx), "consultas")
```

**Resultado medido después:** 2 consultas.

**Explicación de la corrección:** Con prefetch_related bajó a 2. Django hace una consulta para los libros y una segunda con todos los autores de esos libros a la vez, y luego los reparte entre los libros en Python. Por eso, aunque hubiera cien libros, seguirían siendo 2 consultas.

### 4. ¿Por qué select_related no sirve para el caso de los libros y sus autores?

select_related no sirve para libros y autores porque solo funciona cuando cada objeto apunta a uno solo, como un préstamo que tiene un solo estudiante. Un libro tiene varios autores, y un JOIN repetiría el libro una vez por cada autor, así que no se puede traer como lista en una sola consulta. Lo probé en el shell y Django lo rechaza con un error, que dice que autores no es válido y solo acepta categoria. Para esos casos se usa prefetch_related, que hace una consulta aparte y junta los resultados en Python.

### 5. Tabla de resultados

| Consulta | Número de consultas antes | Número de consultas después |
|---|---|---|
| Préstamos con su estudiante y su libro (select_related) | 22 | 1 |
| Libros con la lista de sus autores (prefetch_related) | 7 | 2 |
