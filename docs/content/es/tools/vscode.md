---
title: Extensión de VSCode
description: Extensión de VisualStudio Code para trabajar con componentes Jx
---

Si usas VisualStudio Code, instala la [extensión Jinja-Jx](https://github.com/jpsca/jx-vscode){target="_blank"}.


## Resaltado de sintaxis

La extensión provee resaltado de sintaxis completo para archivos `.jx`, incluyendo:

- Pragmas de Jx: `{#import ... #}`, `{#def ... #}`, `{#css ... #}`, `{#js ... #}`
- Etiquetas de componentes en PascalCase (por ejemplo, `<MyComponent>`, `<Card />`)
- Expresiones (`{{ ... }}`), sentencias (`{% ... %}`) y comentarios (`{# ... #}`) de Jinja2
- HTML estándar (heredado de la gramática HTML integrada de VS Code)

![Extensión Jinja-Jx](/assets/images/vscode.png)


## Ve a la definición

<kbd>Ctrl</kbd>+clic (o <kbd>Cmd</kbd>+clic en macOS) para saltar al archivo de un componente. Esto funciona desde tres lugares:

- **La ruta de importación** — haz clic en la cadena dentro de `{#import "card.jx" as Card #}`
- **El nombre del alias** — haz clic en `Card` en la declaración de importación
- **Una etiqueta de componente** — haz clic en `<Card>` o `</Card>` en cualquier parte de la plantilla

La extensión resuelve rutas usando las carpetas de tu catálogo (autodetectadas desde archivos Python), rutas relativas (`./`, `../`) y rutas con prefijo (`@ui/modal.jx`).


## Diagnósticos

La extensión ejecuta `jx check` automáticamente y muestra los errores en línea en el editor. Las verificaciones se ejecutan:

- Al guardar (archivos `.jx` y `.py`)
- Al abrir un archivo `.jx`
- Al iniciar

![Extensión Jinja-Jx](/assets/images/vscode-didyoumeant.png)

Los errores aparecen en el panel **Problems** y como subrayados en rojo en el editor, incluyendo sugerencias del tipo "¿quisiste decir?" para errores tipográficos.

Esto usa el mismo verificador que el [validador de CLI](/docs/tools/check/) — consulta esa página para detalles sobre lo que se verifica.


## Snippets

Escribe un prefijo y presiona <kbd>Tab</kbd> para expandirlo:

Prefijo    | Se expande a
---------- | -----------------------------
`jximport` | `{#import "..." as ... #}`
`jxdef`    | `{#def ... #}`
`jxcss`    | `{#css ... #}`
`jxjs`     | `{#js ... #}`
`jxslot`   | `{% slot name %} ... {% endslot %}`
`jxfill`   | `{% fill name %} ... {% endfill %}`
`jxcomp`   | Esqueleto completo de componente (import, css, js, def)


## Formateo

La extensión provee formateo de documento (<kbd>Shift</kbd>+<kbd>Alt</kbd>+<kbd>F</kbd>) delegando al formateador HTML integrado de VS Code. Se respetan tus ajustes de formateo HTML (indentación, ajuste de líneas, etc.).


## Autodetección

La extensión escanea automáticamente tu workspace en busca de archivos Python que usen `Catalog()` o `.add_folder()` para detectar:

- Rutas de carpetas de componentes (usadas por ir a la definición)
- Rutas de importación del catálogo (usadas por los diagnósticos)

Si no se encuentra ninguna llamada a `Catalog()`, recurre a buscar archivos `.jx` dentro de carpetas con nombres conocidos (`views`, `components`, `templates`).

El escaneo se vuelve a ejecutar cada vez que se crea, modifica o elimina un archivo `.py`.


## Instalación

Abre VSCode Quick Open (<kbd>Ctrl</kbd>+<kbd>P</kbd>), pega el siguiente comando y presiona ENTER.

```bash
ext install jpscaletti.jinja-jx
```

Alternativamente:

1. Descarga el archivo `jinja-jx-VERSION.vsix` desde el [repositorio de GitHub](https://github.com/jpsca/jx-vscode){target="_blank"}
2. Abre VSCode Quick Command (<kbd>Shift</kbd>+<kbd>Ctrl</kbd>+<kbd>P</kbd>)
3. Ejecuta "Extensions: Install from VSIX..."


## Configuración

Todos los ajustes son opcionales — la extensión funciona sin configuración gracias a la autodetección.

Ajuste             | Por defecto | Descripción
------------------ | ----------- | ----------------------
`jx.check.enabled` | `true`      | Habilita o deshabilita los diagnósticos
`jx.pythonPath`    | `""`        | Ruta al intérprete de Python. Se autodetecta desde la extensión de Python o desde `PATH` si está vacío
`jx.catalogPath`   | `""`        | Ruta de importación a tu instancia de Catalog (por ejemplo, `myapp.setup:catalog`). Se autodetecta si está vacío
