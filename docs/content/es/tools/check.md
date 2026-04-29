---
title: Validador
description: Herramientas de línea de comandos para validar componentes Jx
---

Jx incluye una herramienta de línea de comandos para validar tus componentes. Esto ayuda a detectar errores temprano y puede ser especialmente útil en pipelines de CI.

Apunta el verificador a tu instancia de catálogo usando su ruta de importación de Python. El formato es `module.path:attribute` — el módulo se importa y el atributo se usa como la instancia de `Catalog`.

```sh
$ jx check myapp.setup:catalog
```

También puedes usar `path/to/file.py:attribute` — el archivo se importa y el atributo se usa como la instancia de `Catalog`.

```sh
$ jx check docs/docs.py:catalog
```


## Qué verifica

El comando `check` va más allá de la validación que hace el catálogo al cargar componentes:

1. **Validación entre componentes** — verifica que las rutas de importación (por ejemplo `{#import "buton.jx" ...}`) realmente resuelvan a componentes del catálogo. El catálogo solo verifica que las importaciones existan en el momento del renderizado.
2. **Detección de etiquetas no importadas** — encuentra etiquetas en PascalCase como `<Button />` que no están importadas pero existen en el catálogo ("usado pero no importado").
3. **Sugerencias** — "¿quisiste decir 'button.jx'?" / "¿quisiste decir 'Button'?" para errores tipográficos.
4. **Recolecta todos los errores** — check reporta cada problema en cada componente.
5. **Salida JSON estructurada** — para integración con IDE (la extensión de VS Code la usa).


## Formatos de salida

### Texto (por defecto)

```sh
$ jx check myapp.setup:catalog
```

```sh
✓ button.jx - OK
✓ card.jx - OK
✗ page.jx:12 - Component 'Buton' used but not imported (did you mean 'Button'?)
✗ modal.jx - Unknown import 'dialog.jx' (did you mean 'dialogs/dialog.jx'?)

4 components checked, 2 errors
```

### JSON

```sh
$ jx check --format json myapp.setup:catalog
```

```json
{
  "checked": 4,
  "errors": [
    {
      "file": "page.jx",
      "abs_path": "/path/to/components/page.jx",
      "line": 12,
      "message": "Component 'Buton' used but not imported",
      "suggestion": "Button"
    },
    {
      "file": "modal.jx",
      "abs_path": "/path/to/components/modal.jx",
      "line": null,
      "message": "Unknown import 'dialog.jx'",
      "suggestion": "dialogs/dialog.jx"
    }
  ]
}
```

La salida JSON es útil para integrar con editores, linters o herramientas personalizadas.

## Uso programático

También puedes usar el verificador desde código Python:

```python
from jx import Catalog
from jx.tools import check, check_all

catalog = Catalog("components/")

# Obtén errores estructurados
errors, checked = check_all(catalog)
for error in errors:
    print(f"{error.file}:{error.line} - {error.message}")

# O ejecutar la verificación completa con salida formateada (devuelve el código de salida)
exit_code = check(catalog, format="text")
```
