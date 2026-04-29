---
title: Componentes
description: Construyendo componentes con Jx
---

Un componente es un fragmento de plantilla reutilizable que funciona como una función. Puede recibir argumentos, renderizar contenido y componerse con otros componentes para construir UIs complejas.

Piensa en los componentes como los bloques de construcción de tu interfaz: botones, tarjetas, formularios, layouts; cualquier cosa que uses más de una vez o que quieras mantener organizada.

## Crea un componente

Los componentes son archivos de plantilla Jinja con extensión `.jx`:

```html+jinja title="components/button.jx"
{#def text #}

<button class="btn">{{ text }}</button>
```

### Anatomía de un componente

Un componente completo puede tener estas partes:

```html+jinja title="components/card.jx"
{#import "./header.jx" as Header #}
{#css card.css #}
{#js card.js #}
{#def title, subtitle="" #}

<div class="card">
  <Header title={{ title }} subtitle={{ subtitle }} />
  <div class="card-body">
    {{ content }}
  </div>
</div>
```

De arriba a abajo:

1. **Importaciones** - Otros componentes que este utiliza
2. **Assets** - Archivos CSS y JS
3. **Argumentos** - Datos que el componente acepta
4. **Plantilla** - El HTML a renderizar

Todas las partes son opcionales excepto la plantilla.

## Usa componentes

Importa un componente y úsalo como una etiqueta HTML:

```html+jinja
{#import "button.jx" as Button #}
{#import "card.jx" as Card #}

<Card title="Bienvenido">
  <p>¡Hola mundo!</p>
  <Button text="Haz clic" />
</Card>
```

**Sintaxis de bloque** para componentes con contenido:

```html+jinja
<Card title="Hola">
  <p>El contenido va aquí</p>
</Card>
```

**Sintaxis auto-cerrada** para componentes sin contenido:

```html+jinja
<Button text="Haz clic" />
```

---

## Importaciones

Jx requiere importaciones explícitas antes de usar componentes.

### Sintaxis básica

```html+jinja
{#import "path/to/component.jx" as Name #}
```

### Nombrado de archivos

Los archivos y carpetas de componentes pueden usar cualquier convención de nombrado: `button.jx`, `user-card.jx`, `form_input.jx`, etc. Sin embargo, el **alias de importación** debe estar en `PascalCase` para distinguir los componentes del HTML:

```html+jinja
{#import "user-card.jx" as UserCard #}
{#import "form_input.jx" as FormInput #}

<UserCard />   {# Componente #}
<div />        {# HTML #}
```

### Importaciones absolutas

Rutas relativas a una carpeta del catálogo:

```html+jinja
{#import "components/button.jx" as Button #}
{#import "layouts/base.jx" as Base #}
```

Úsalas para componentes compartidos a lo largo de tu proyecto.

### Importaciones relativas

Rutas relativas al archivo actual:

```html+jinja
{#import "./sibling.jx" as Sibling #}
{#import "../parent/component.jx" as Component #}
{#import "./subfolder/child.jx" as Child #}
```

Úsalas para componentes estrechamente relacionados. Mueve una carpeta entera y las importaciones internas seguirán funcionando.

**Estructura de ejemplo:**

```
components/
  modal/
    modal.jx       {#import "./header.jx" as Header #}
    header.jx      {#import "./close-btn.jx" as CloseBtn #}
    close-btn.jx
```

### Importaciones con prefijo

Para componentes desde carpetas del catálogo con prefijo:

```python
catalog.add_folder("vendor/ui-lib", prefix="ui")
```

```html+jinja
{#import "@ui/button.jx" as Button #}
{#import "@ui/modal.jx" as Modal #}
```

Úsalas para librerías de componentes de terceros.

---

## Argumentos

Los componentes aceptan argumentos para personalizar su comportamiento.

### Declara argumentos

Usa `{#def ... #}` al inicio de tu componente:

```html+jinja
{#def title, count=0 #}

<h2>{{ title }}: {{ count }}</h2>
```

- `title` - Requerido (sin valor por defecto)
- `count` - Opcional (por defecto `0`)


#### Anotaciones de tipo

Los argumentos también pueden tener anotaciones de tipo:

```html+jinja                                                                                           
{#def
    title: str,
    count: int = 0,
    items: list[str] = [],
    data: dict[str, int] = {}
#}
```

Para tipos primitivos (`int`, `str`, `bool`, `list`, `dict`, etc.), Jx valida en tiempo de ejecución que los argumentos pasados coincidan con los tipos declarados.

**Sin embargo, esto se limita a tipos simples**. Por ejemplo, para argumentos con tipos como `list[str]`, Jx solo verifica que el argumento sea una lista, no que sus elementos sean cadenas. Lo mismo aplica para `dict[str, int]`, `tuple[int, ...]`, etc. Tampoco puede verificar tipos unión como `int | str`.


### Valores por defecto

Los valores por defecto pueden ser cualquier valor de Python: cadenas, números, booleanos, listas, diccionarios, etc.

```html+jinja
{#def
  name,
  count=0,
  active=true,
  items=[],
  config={}
#}
```

### Pasa argumentos

Las **cadenas** usan comillas:

```html+jinja
<Button text="Haz clic" />
```

Las **expresiones** usan `{{ }}`:

```html+jinja
<Card
  user={{ current_user }}
  count={{ items | length }}
  active={{ true }}
  items={{ [1, 2, 3] }}
/>
```

Los **booleanos** pueden usar la forma corta tipo HTML para `true`:

```html+jinja
<Input required />          {# Igual que required={{ true }} #}
<Input disabled={{ false }} />
```

### De guion a guion bajo

Los guiones en los nombres de atributos se convierten en guiones bajos:

```html+jinja
{#def aria_label, data_id #}

<Button aria-label="Cerrar" data-id="123" />
```

Tanto `aria-label` como `aria_label` coinciden con `aria_label` en la def.

---

## Contenido y slots

Los componentes pueden envolver contenido pasado entre sus etiquetas.

### La variable `content`

Todo lo que esté entre las etiquetas de un componente está disponible como `content`:

```html+jinja title="components/card.jx"
{#def title #}

<div class="card">
  <h3>{{ title }}</h3>
  <div class="body">{{ content }}</div>
</div>
```

```html+jinja title="uso"
<Card title="Hola">
  <p>¡Esto se convierte en el contenido!</p>
</Card>
```

### Contenido de respaldo

Provee valores por defecto cuando no se pasa contenido:

```html+jinja
<div class="body">
  {{ content or "No se proporcionó contenido" }}
</div>
```

### Slots con nombre

Para múltiples áreas de contenido, usa slots con nombre.

**Define los slots** en el componente con `{% slot %}`:

```html+jinja title="components/modal.jx"
<div class="modal">
  <div class="modal-header">
    {% slot header %}
      <h3>Encabezado por defecto</h3>
    {% endslot %}
  </div>
  <div class="modal-body">
    {{ content }}
  </div>
  <div class="modal-footer">
    {% slot footer %}
      <button>Cerrar</button>
    {% endslot %}
  </div>
</div>
```

**Llena los slots** al usar el componente con `{% fill %}`:

```html+jinja title="uso"
<Modal>
  {% fill header %}
    <h3>Confirmar</h3>
  {% endfill %}

  <p>¿Estás seguro?</p>

  {% fill footer %}
    <button>Sí</button>
    <button>No</button>
  {% endfill %}
</Modal>
```

Los slots no llenados usan su contenido por defecto.

### Cuándo usar slots vs props

#### Usa props cuando:

- El contenido es un valor único
- Quieres validación

```html+jinja
{#def title, count #}
<h2>{{ title }}: {{ count }}</h2>
```

#### Usa content cuando:

- El contenido es HTML
- Hay un área principal de contenido
- Quieres flexibilidad en lo que se pasa

```html+jinja
{#def title #}
<div class="card">
  <h2>{{ title }}</h2>
  {{ content }}
</div>
```

#### Usa slots con nombre cuando:

- Necesitas múltiples áreas de contenido
- Cada área tiene un propósito específico
- Podrías querer proveer valores por defecto para cada área

```html+jinja
<div class="panel">
  <header>{% slot header %}Por defecto{% endslot %}</header>
  <main>{{ content }}</main>
  <footer>{% slot footer %}Por defecto{% endslot %}</footer>
</div>
```

## Validación

Jx incluye una herramienta CLI para validar todos tus componentes a la vez:

```bash
❯❯ jx check myapp.setup:catalog
```

Esto detecta errores de importación, etiquetas no importadas, errores de tipeo y más. Consulta la página del [Validador](/docs/tools/check/) para más detalles.
