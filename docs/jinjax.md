Jx is a total rewrite of JinjaX. It's at least 10% faster, slighty smaller, and much more elegant/

## Imports manuales

La diferencia más grande entre usar JinjaX y Jx es esta.

### JinjaX

En JinjaX no era necesario importar los components antes de usarlos. El nombre de cada componente dependia de donde estaban en el sistema de archivos. Por ejemplo:

```python
from jinjax import Catalog

catalog = Catalog()
catalog.add_folder("views/")
catalog.add_folder("components")
```

```html+jinja
{#def comment #}
<UI.Card>
  <Comments.Header>{{ comment.author }}</Comments.Header>
  <Comments.Body>{{ comment.body }}</Comments.Body>
  <div>
    <UI.Button><UI.Icon name="reply" /> Reply</UI.Button>
  </div>
</UI.Card>
```

Este omponente usa estos otros:

* `views/layouts/private.jinja`
* `views/comments/header.jinja`
* `views/comments/body.jinja`
* `components/ui/button.jinja`
* `components/ui/card.jinja`
* `components/ui/icon.jinja`

### Jx

En Jx, los imports tienen que ser explícitos, usando `{# import xxx.jinja as Name #}`:

```html+jinja
{# import "ui/button.jinja" as Button #}
{# import "ui/card.jinja" as Card #}
{# import "ui/icon.jinja" as Icon #}
{# import "comments/header.jinja" as Header #}
{# import "comments/body.jinja" as Body #}
{#def comment #}

<Card>
  <Header comment={{ comment }} />
  <Body>{{ comment.body }}</Body>
  <div>
    <Button><Icon name="reply" /> Reply</Button>
  </div>
</Card>
```

Nota como el nombre depende de ti, no del nombre de los nombres de los archivos de los componentes.

La rutas también pueden ser relativas:

```html+jinja {title="comments/comment.jinja", hl_lines="4 5"}
{# import "ui/button.jinja" as Button #}
{# import "ui/card.jinja" as Card #}
{# import "ui/icon.jinja" as Icon #}
{# import "./header.jinja" as Header #}
{# import "./body.jinja" as Body #}
{#def comment #}

<Card>
  <Header comment={{ comment }} />
  <Body>{{ comment.body }}</Body>
  <div>
    <Button><Icon name="reply" /> Reply</Button>
  </div>
</Card>
```

### Motivación

Aunque parece que no tener que manualmente importar los componentes que usas es más práctico por que escribes menos, en realidad es lo contrario.

En casi cualquier proyecto, la cantidad de componentes crece rapidamente. Tener decenas (o cientos) de componentes en un solo folder te hace más dificil encontrar uno en particular y las colisiones de nombres se vuelven un problema. Asi que lo natural es categorizarlos en folders: creas components como `pages/products/show.jinja`, `comments/show.jinja`, y `commom/forms/input.jinja`, etc. pero tus plantillas se vuelven mucho, mucho mas verbosas.



Además, porque permite imports relativos al componente actual, se pueden escribir componentes compuestos independientes del resto del proeycto, algo que intenté hacer en JinjaX con prefijos, pero con imports relativos es mucho mas simple y directo.


## `Catalog.render()` usa rutas de archivos en vez de nombres

