---
title: Inicio rápido
---

## Instala Jx

Ejecuta el siguiente comando:

::: tab | Usando "**pip**"

```bash
pip install jx
```

:::

::: tab | Usando "**uv**"

```bash
uv add jx
```

:::

## Crea un catálogo

```python {title="app.py"}
from jx import Catalog

catalog = Catalog("components/")
```

## Crea un componente

Crea una nueva carpeta para tus componentes. Dentro de esta carpeta crea un nuevo archivo llamado `card.jx` con el siguiente contenido:

```html+jinja {title="components/card.jx"}
{#def title, url #}

<div class="bg-white shadow rounded border p-4">
  <h2 class="m-0 text-gray-800">{{ title }}</h2>
  <p>{{ content }}</p>
  <a href="{{ url }}" class="text-teal-600">Leer más</a>
</div>
```

## Usa el componente

```python {title="views.py"}
from .app import catalog

def dashboard_view():
    return catalog.render("dashboard.jx")
```

```html+jinja {title="components/dashboard.jx"}
{#import "card.jx" as Card #}

<Card title="Árboles" url="trees">
  Tenemos los mejores árboles
</Card>

<Card title="Palas" url="spades">
  Las mejores palas de la región
</Card>
```

::: tab | Vista previa
<div class="demo">
<div class="bg-white shadow rounded border p-4 mb-3">
  <h2 class="m-0 text-gray-800">Árboles</h2>
  <p>Tenemos los mejores árboles</p>
  <a href="/trees" class="text-teal-600">Leer más</a>
</div>
<div class="bg-white shadow rounded border p-4 mb-3">
  <h2 class="m-0 text-gray-800">Palas</h2>
  <p>Las mejores palas de la región</p>
  <a href="/spades" class="text-teal-600">Leer más</a>
</div>
</div>
:::

::: tab | HTML

```html
<div class="bg-white shadow rounded border p-4 mb-3">
  <h2 class="m-0 text-gray-800">Árboles</h2>
  <p>Tenemos los mejores árboles</p>
  <a href="/trees" class="text-teal-600">Leer más</a>
</div>
<div class="bg-white shadow rounded border p-4 mb-3">
  <h2 class="m-0 text-gray-800">Palas</h2>
  <p>Las mejores palas de la región</p>
  <a href="/spades" class="text-teal-600">Leer más</a>
</div>
```

:::
