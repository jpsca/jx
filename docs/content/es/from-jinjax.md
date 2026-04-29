---
title: Migra de JinjaX a Jx
---

## ¿Por qué Jx?

Jx toma todo lo que hizo grande a JinjaX y lo mejora apostando por la explicitud, la simplicidad y patrones familiares. El resultado es código más fácil de escribir, más fácil de entender y más fácil de mantener.

Dale una oportunidad a Jx; creemos que vas a apreciar la claridad.


## Filosofía: lo explícito es mejor que lo implícito

El cambio más grande en Jx es exigir **importaciones explícitas**. Si bien el descubrimiento automático de JinjaX se siente conveniente al principio, las importaciones explícitas brindan beneficios sustanciales que se vuelven invaluables a medida que tu proyecto crece.

## Diferencias clave

### 1. Importaciones explícitas de componentes

**JinjaX:**
```html+jinja
{#def products #}
<Layout title="Products">
  <Common.UI.Card>
    {% for product in products %}
      <Common.UI.ProductCard product={{ product }} />
    {% endfor %}
  </Common.UI.Card>
</Layout>
```

**Jx:**
```html+jinja
{#import "layout.jx" as Layout #}
{#import "common/ui/card.jx" as Card #}
{#import "common/ui/product-card.jx" as ProductCard #}
{#def products #}

<Layout title="Products">
  <Card>
    {% for product in products %}
      <ProductCard product={{ product }} />
    {% endfor %}
  </Card>
</Layout>
```

**Por qué esto es mejor:**

- **Dependencias claras**: puedes ver de un vistazo qué componentes usa un archivo; no hay que buscar referencias de componentes a lo largo de la plantilla
- **Sin contaminación del namespace**: tú controlas los nombres. Un `common/forms/inputs/text-input.jx` profundamente anidado puede importarse simplemente como `TextInput`
- **Mejores mensajes de error**: las importaciones faltantes fallan inmediatamente al cargar, no al renderizar
- **Práctica estándar**: sigue el mismo patrón que los módulos de Python, las importaciones de JavaScript y prácticamente cualquier lenguaje moderno
- **Mejor soporte del IDE**: tu editor puede autocompletar importaciones, saltar a definiciones y ayudar al refactorizar

**Nota sobre los nombres de archivos:** los archivos de componentes pueden usar cualquier convención de nombres que prefieras (kebab-case, snake_case, PascalCase). Solo el alias de importación (la parte `as ComponentName`) debe estar en PascalCase para distinguir los componentes de las etiquetas HTML.

#### Importaciones relativas: aún mejor

Jx también admite **importaciones relativas**, algo que JinjaX no tiene en absoluto. Esto cambia las reglas del juego para la organización de componentes:

```html+jinja
{# components/user/profile-card.jx #}
{#import "./avatar.jx" as Avatar #}
{#import "./bio.jx" as Bio #}
{#import "../common/card.jx" as Card #}

<Card class="profile-card">
  <Avatar user={{ user }} />
  <Bio user={{ user }} />
</Card>
```

**Por qué las importaciones relativas son potentes:**

- **Portabilidad**: mueve una carpeta entera de componentes relacionados y todas las importaciones internas siguen funcionando; no hay que actualizar rutas
- **Encapsulación**: los componentes pueden referenciar a sus hermanos sin conocer la estructura global de carpetas
- **Relaciones más claras**: `./sibling.jx` muestra inmediatamente un acoplamiento local; `../parent/` muestra que estás subiendo un nivel
- **Bibliotecas de componentes**: construye paquetes de componentes reutilizables que funcionan independientemente de dónde estén instalados
- **Menos frágiles**: refactorizar la estructura general de carpetas no rompe las importaciones dentro de los grupos de componentes

**Ejemplo: un grupo de componentes Modal portable**

```
components/
  modal/
    modal.jx          {#import "./header.jx" as Header #}
    header.jx         {#import "./close-button.jx" as CloseButton #}
    body.jx
    footer.jx
    close-button.jx
```

Mueve la carpeta `modal/` completa a donde quieras y todas las importaciones internas seguirán funcionando. Con el namespace global de JinjaX, tendrías que actualizar cada referencia.

### 2. Gestión de assets más simple

**JinjaX:**
```python
# Requires middleware setup
app.wsgi_app = catalog.get_middleware(
    app.wsgi_app,
    autorefresh=app.debug,
)
```

```html+jinja
{#css mypage.css #}
{#js mypage.js #}

<Layout title="My Page">
  {{ catalog.render_assets() }}
  ...
</Layout>
```

**Jx:**
```html+jinja
{#css mypage.css #}
{#js mypage.js #}

<Layout title="My Page">
  {{ assets.render() }}
  ...
</Layout>
```

**Por qué esto es mejor:**

- **No requiere middleware**: las URLs de los assets se renderizan tal cual. Tú las sirves de la forma que tenga sentido para tu aplicación
- **API más limpia**: `assets.render()` en lugar de `catalog.render_assets()`; el objeto `assets` es un global natural en el contexto de la plantilla
- **Más flexible**: ¿quieres usar Vite? ¿Webpack? ¿Un CDN? Solo referencia las URLs directamente; Jx no las procesa ni las reescribe
- **Control granular**: usa `assets.collect_css()` y `assets.collect_js()` para tener control total, o `assets.render_css()` / `assets.render_js()` para mayor comodidad

### 3. Mejor sintaxis de slots

**JinjaX (slots con nombre):**
```html+jinja
{# En el padre #}
<Modal>
  {% if _slot == "header" %}
    My Custom Header
  {% elif _slot == "body" %}
    My Body
  {% elif _slot == "footer" %}
    My Footer
  {% endif %}
</Modal>
```

**Jx:**
```html+jinja
{# En el padre #}
<Modal>
  {% fill header %}
    My Custom Header
  {% endfill %}

  <p>My Body</p>

  {% fill footer %}
    My Footer
  {% endfill %}
</Modal>

{# En modal.jx #}
<div class="modal">
  <div class="modal-header">
    {% slot header %}Default Header{% endslot %}
  </div>
  <div class="modal-body">
    {{ content }}
  </div>
  <div class="modal-footer">
    {% slot footer %}Default Footer{% endslot %}
  </div>
</div>
```

**Por qué esto es mejor:**

- **Autodocumentado**: `{% fill header %}` muestra claramente que estás llenando un slot con nombre
- **Valores por defecto en los componentes**: los valores por defecto de los slots viven en el componente, donde corresponde
- **Menos magia**: nada de revisar variables `_slot`; los slots y los fills son explícitos
- **Anidamiento más limpio**: mezcla contenido normal con slots con nombre de forma natural

### 4. Sistema de prefijos más simple

**JinjaX:**
```python
catalog.add_folder("components")  # Components use dot notation
catalog.add_folder("vendor/ui", prefix="ui")  # Prefix with colon
```
```html+jinja
<common.Card />      {# Desde components/common/Card.jx #}
<ui:Button />        {# Desde vendor/ui/Button.jx #}
```

**Jx:**
```python
catalog.add_folder("components")
catalog.add_folder("vendor/ui", prefix="ui")
```
```html+jinja
{#import "common/card.jx" as Card #}
{#import "@ui/button.jx" as Button #}

<Card />
<Button />
```

Nota: los **archivos** de componentes pueden nombrarse con cualquier convención (kebab-case, snake_case, etc.). Solo el **alias** de importación necesita estar en PascalCase.

**Por qué esto es mejor:**

- **Sintaxis consistente**: todos los prefijos usan la notación `@prefix/`; sin mezclar puntos y dos puntos
- **Importa una vez, usa en cualquier parte**: la importación maneja el prefijo, el uso del componente se mantiene limpio
- **Pertenencia clara**: `@ui/` indica inmediatamente que esto viene de una carpeta con prefijo

## Lo que se mantiene igual

Todas las grandes partes de JinjaX permanecen:

- **Arquitectura basada en componentes** para organizar plantillas
- **CSS/JS encapsulado** por componente
- **El objeto `attrs`** para el manejo flexible de atributos
- **Props con valores por defecto** usando `{#def name, title="Default" #}`
- **Slots de contenido** para componibilidad
- **Funciona muy bien con htmx, Alpine.js y TailwindCSS**


## En resumen

Jx cambia un poco de comodidad inicial (descubrimiento automático) por beneficios significativos a largo plazo:

- **Código más claro** (dependencias explícitas, sin magia)
- **Depuración más fácil** (errores de importación en vez de errores en tiempo de ejecución)
- **Más flexibilidad** (especialmente para los assets)
- **Patrones familiares** (las importaciones funcionan como en Python, JavaScript, etc.)
- **Importaciones relativas** (portabilidad y encapsulación que JinjaX no puede igualar)
- **Mejor soporte de herramientas** (navegación y refactorización)

Si estás construyendo algo más allá de un proyecto de juguete, estos beneficios se acumulan rápidamente. Las importaciones explícitas hacen tu base de código más mantenible, más comprensible para los nuevos desarrolladores y más fácil de refactorizar a medida que crece.

## Ejemplo: comparación con un caso real

**Enfoque JinjaX:**
```html+jinja
{#def user, posts #}
<Layouts.App title="User Profile">
  <Components.User.ProfileCard user={{ user }}>
    <Components.User.Avatar user={{ user }} size="large" />
  </Components.User.ProfileCard>

  <Components.Feed.PostList>
    {% for post in posts %}
      <Components.Feed.PostCard post={{ post }} />
    {% endfor %}
  </Components.Feed.PostList>
</Layouts.App>
```

- Difícil saber dónde viven estos componentes
- No hay forma de saber si existen hasta el tiempo de ejecución
- Renombrar `Components.User.ProfileCard` significa encontrar todas las referencias manualmente
- Los namespaces anidados son verbosos y repetitivos

**Enfoque Jx:**
```html+jinja
{#import "layouts/app.jx" as App #}
{#import "components/user/profile-card.jx" as ProfileCard #}
{#import "components/user/avatar.jx" as Avatar #}
{#import "components/feed/post-list.jx" as PostList #}
{#import "components/feed/post-card.jx" as PostCard #}
{#def user, posts #}

<App title="User Profile">
  <ProfileCard user={{ user }}>
    <Avatar user={{ user }} size="large" />
  </ProfileCard>

  <PostList>
    {% for post in posts %}
      <PostCard post={{ post }} />
    {% endfor %}
  </PostList>
</App>
```

- Dependencias claras listadas en la parte superior
- Nombres de componentes limpios sin namespacing repetitivo
- Los errores de importación fallan rápido al cargar

**Aún mejor con importaciones relativas:**

Si tus componentes de usuario están organizados en `components/user/`, puedes hacerlos más portables:

```html+jinja
{#import "layouts/app.jx" as App #}
{#import "./profile-card.jx" as ProfileCard #}
{#import "./avatar.jx" as Avatar #}
{#import "components/feed/post-list.jx" as PostList #}
{#import "components/feed/post-card.jx" as PostCard #}
{#def user, posts #}

<App title="User Profile">
  <ProfileCard user={{ user }}>
    <Avatar user={{ user }} size="large" />
  </ProfileCard>

  <PostList>
    {% for post in posts %}
      <PostCard post={{ post }} />
    {% endfor %}
  </PostList>
</App>
```

Ahora, si reorganizas los componentes de usuario, solo las importaciones de este archivo necesitan actualizarse; las dependencias internas entre `ProfileCard` y `Avatar` permanecen intactas.


## ⚡ Guía de migración

### Migra los componentes

:::tip | Usa la herramienta de migración
El script [jx-migrate](https://github.com/jpsca/jx-migrate) puede escanear tu carpeta de componentes, verificar qué cambios son necesarios y hacer la migración automáticamente por ti.

Aún así vas a tener que migrar el código de Python manualmente. [Mira las instrucciones más abajo](#migrating-python-code).

Ejecuta `uvx https://raw.githubusercontent.com/jpsca/jx-migrate/main/migrate.py` y sigue las instrucciones.
:::

Si prefieres hacer la migración de los componentes a mano, sigue estos pasos.

#### Paso 1: cambia la extensión de los archivos de plantilla

Jx usa la extensión `.jx` por defecto, así que, idealmente, deberías cambiar los nombres de tus archivos de plantilla de `name.jinja` a `name.jx`.

Alternativamente, puedes seguir usando `.jinja` declarándolo en el catálogo:

```python
catalog = Catalog(..., file_ext=".jinja")
```
#### Paso 2: agrega importaciones

Recorre cada componente y agrega importaciones explícitas en la parte superior:

```diff
+ {#import "components/card.jx" as Card #}
+ {#import "components/button.jx" as Button #}

  <Card>
    <Button>Click me</Button>
  </Card>
```

**Tip**: usa importaciones relativas para los componentes en la misma carpeta o cercanos:

```html+jinja
{# Para hermanos en la misma carpeta #}
{#import "./sibling.jx" as Sibling #}

{# Para componentes en una carpeta padre #}
{#import "../common/helper.jx" as Helper #}

{# Para componentes en una subcarpeta #}
{#import "./parts/detail.jx" as Detail #}
```

Esto hace que tus componentes sean más portables y fáciles de reorganizar.

#### Paso 3: reemplaza las referencias de componentes

Cambia los nombres de componentes con notación de puntos por nombres importados:

```diff
- <Common.UI.Card>
+ <Card>
```

#### Paso 4: actualiza el renderizado de assets

```diff
- {{ catalog.render_assets() }}
+ {{ assets.render() }}
```

O usa los métodos más granulares:

```html+jinja
{{ assets.render_css() }}
{{ assets.render_js(module=True) }}
```

#### Paso 5: actualiza los slots con nombre (si los usas)

Reemplaza los condicionales con `_slot` por bloques `{% fill %}`:

```diff
  {# Componente padre #}
  <Modal>
-   {% if _slot == "header" %}
-     My Header
-   {% endif %}
+   {% fill header %}
+     My Header
+   {% endfill %}

    <p>Body content</p>
  </Modal>
```

```diff
  {# modal.jx #}
  <div class="modal-header">
-   {{ content("header") }}
+   {% slot header %}Default Header{% endslot %}
  </div>
  <div class="modal-body">
    {{ content }}
  </div>
```

### Migra el código de Python
{#migrating-python-code}

Después de ejecutar el script de migración, necesitas actualizar tu código de integración con Python. Esto es lo que cambia para cada framework.

#### 1. Reemplaza el paquete

```bash
pip uninstall jinjax
pip install jx
```

#### 2. Actualiza las importaciones

```python
# Before
import jinjax
# or
from jinjax import Catalog, JinjaX

# After
import jx
# or
from jx import Catalog
```

#### 3. Actualiza la construcción del Catalog

El `Catalog` de JinjaX recibe todos sus parámetros como argumentos por nombre. El `Catalog` de Jx acepta un atajo posicional `folder` y pasa los globales como `**kwargs`.

```python
# Before (JinjaX)
catalog = jinjax.Catalog(
    globals={"site_name": "My Site"},
)
catalog.add_folder("components/")

# After (Jx)
catalog = jx.Catalog(
    "components/",        # optional folder shortcut (new)
    site_name="My Site",  # globals are now **kwargs, not a dict
)
```

Diferencias clave:
- diccionario `globals={"key": val}` → se pasan como `**kwargs` directamente: `key=val`
- `root_url`, `file_ext`, `use_cache`, `fingerprint` → eliminados (Jx no sirve assets)
- `folder` → primer argumento posicional opcional (atajo para `add_folder`)

#### 4. Actualiza las llamadas a `render`

```python
# Before (JinjaX)
html = catalog.render("ComponentName", arg1="value", arg2=42)
# Component name used dot notation: "common.Form"

# After (Jx)
html = catalog.render("component-name.jx", arg1="value", arg2=42)
# Uses file path with extension: "common/form.jx"
```

Diferencias clave:
- JinjaX usa nombres de componentes en PascalCase con notación de puntos: `"Card"`, `"common.Form"`
- Jx usa rutas de archivo con extensión: `"card.jx"`, `"common/form.jx"`
- Jx también acepta un parámetro `globals` como diccionario para globales por renderizado:

```python
html = catalog.render(
    "page.jx",
    globals={"request": request, "csrf_token": token},
    title="Dashboard",
)
```

#### 5. Elimina el middleware

JinjaX requiere su propio middleware para servir el CSS/JS de los componentes. Jx no — los assets son simplemente URLs servidas por tu configuración existente de archivos estáticos.

```python
# Before (JinjaX) — DELETE THIS
app.wsgi_app = catalog.get_middleware(app.wsgi_app)
```

Asegúrate de que la configuración de archivos estáticos de tu framework web sirva la carpeta que elegiste durante la migración (la carpeta estática) en el prefijo de URL que elegiste.

#### 6. Actualiza los parámetros especiales de render

```python
# Before (JinjaX)
html = catalog.render("Card", _content="<p>Hi</p>", _source="...", _globals={...})
# Also accepted legacy: __content, __source, __globals

# After (Jx) — these don't exist
# Usa catalog.render_string() para código en línea:
html = catalog.render_string("{#def name #}<p>{{ name }}</p>", name="Hi")
# Pasa los globales mediante el parámetro globals:
html = catalog.render("card.jx", globals={"request": req}, title="Hi")
```

#### Ejemplos específicos por framework

##### Flask

```python
# Before
import jinjax

app = Flask(__name__)
catalog = jinjax.Catalog(jinja_env=app.jinja_env)
catalog.add_folder("components")
app.wsgi_app = catalog.get_middleware(app.wsgi_app, autorefresh=app.debug)

@app.route("/")
def index():
    return catalog.render("Page", title="Home")

# After
import jx

app = Flask(__name__)
catalog = jx.Catalog("components", jinja_env=app.jinja_env)

@app.route("/")
def index():
    return catalog.render("page.jx", title="Home")
```

##### Django (con django-jinja o configuración manual de Jinja2)

```python
# Before
import jinjax

env.add_extension(jinjax.JinjaX)
catalog = jinjax.Catalog(jinja_env=env)
catalog.add_folder("components")

# After
import jx

catalog = jx.Catalog("components", jinja_env=env)
```

##### FastAPI

```python
# Before
import jinjax

templates = Jinja2Templates(directory="templates")
templates.env.add_extension(jinjax.JinjaX)
catalog = jinjax.Catalog(jinja_env=templates.env)
catalog.add_folder("templates/components")

# After
import jx

catalog = jx.Catalog("templates/components", jinja_env=templates.env)
```

#### Lista de verificación resumen

- [ ] Instalar `jx` y desinstalar `jinjax`
- [ ] `import jinjax` → `import jx`
- [ ] `jinjax.Catalog(...)` → `jx.Catalog(...)` con argumentos actualizados
- [ ] diccionario `globals={...}` → `**kwargs`
- [ ] Eliminar los parámetros `root_url`, `file_ext`, `use_cache`, `fingerprint`
- [ ] `catalog.render("ComponentName", ...)` → `catalog.render("component-name.jx", ...)`
- [ ] Eliminar la llamada a `catalog.get_middleware(...)`
- [ ] Configurar tu servidor de archivos estáticos para servir los assets migrados
