---
title: Migrating from JinjaX to Jx
---

## Why Jx?

Jx takes everything that made JinjaX great and makes it better by embracing explicitness, simplicity, and familiar patterns. The result is code that's easier to write, easier to understand, and easier to maintain.

Give Jx a try; we think you'll appreciate the clarity.


## Philosophy: Explicit is Better Than Implicit

The biggest change in Jx is requiring **explicit imports**. While JinjaX's auto-discovery feels convenient at first, explicit imports provide substantial benefits that become invaluable as your project grows.

## Key Differences

### 1. Explicit Component Imports

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

**Why this is better:**

- **Clear Dependencies**: You can see at a glance which components a file uses; no hunting through the template to find component references
- **No Namespace Pollution**: You control the names. A deeply nested `common/forms/inputs/text-input.jx` can be imported as simply `TextInput`
- **Better Error Messages**: Missing imports fail immediately at load time, not at render time
- **Standard Practice**: Follows the same pattern as Python modules, JavaScript imports, and virtually every modern language
- **Better IDE Support**: Your editor can autocomplete imports, jump to definitions, and aid in refactoring

**Note on file naming:** Component files can use any naming convention you prefer (kebab-case, snake_case, PascalCase). Only the import alias (the `as ComponentName` part) must be PascalCase to distinguish components from HTML tags.

#### Relative Imports: Even Better

Jx also supports **relative imports**, which JinjaX doesn't have at all. This is a game-changer for component organization:

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

**Why relative imports are powerful:**

- **Portability**: Move an entire folder of related components and all internal imports still work; no need to update paths
- **Encapsulation**: Components can reference siblings without knowing the global folder structure
- **Clearer Relationships**: `./sibling.jx` immediately shows local coupling; `../parent/` shows you're reaching up
- **Component Libraries**: Build reusable component packages that work regardless of where they're installed
- **Less Brittle**: Refactoring the overall folder structure doesn't break imports within component groups

**Example: A portable Modal component group**

```
components/
  modal/
    modal.jx          {#import "./header.jx" as Header #}
    header.jx         {#import "./close-button.jx" as CloseButton #}
    body.jx
    footer.jx
    close-button.jx
```

Move the entire `modal/` folder anywhere, and all the internal imports still work. With JinjaX's global namespace, you'd have to update every reference.

### 2. Simpler Asset Management

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

**Why this is better:**

- **No Middleware Required**: Asset URLs are rendered as-is. You handle serving them however makes sense for your app
- **Cleaner API**: `assets.render()` instead of `catalog.render_assets()`; the `assets` object is a natural global in the template context
- **More Flexible**: Want to use Vite? Webpack? A CDN? Just reference the URLs directly; Jx doesn't process or rewrite them
- **Granular Control**: Use `assets.collect_css()` and `assets.collect_js()` for full control, or `assets.render_css()` / `assets.render_js()` for convenience

### 3. Better Slot Syntax

**JinjaX (named slots):**
```html+jinja
{# In parent #}
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
{# In parent #}
<Modal>
  {% fill header %}
    My Custom Header
  {% endfill %}

  <p>My Body</p>

  {% fill footer %}
    My Footer
  {% endfill %}
</Modal>

{# In modal.jx #}
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

**Why this is better:**

- **Self-Documenting**: `{% fill header %}` clearly shows you're filling a named slot
- **Defaults in Components**: Slot defaults live in the component where they belong
- **Less Magic**: No checking `_slot` variables; slots and fills are explicit
- **Cleaner Nesting**: Mix regular content with named slots naturally

### 4. Simpler Prefix System

**JinjaX:**
```python
catalog.add_folder("components")  # Components use dot notation
catalog.add_folder("vendor/ui", prefix="ui")  # Prefix with colon
```
```html+jinja
<common.Card />      {# From components/common/Card.jx #}
<ui:Button />        {# From vendor/ui/Button.jx #}
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

Note: Component **files** can be named with any convention (kebab-case, snake_case, etc.). Only the import **alias** needs to be PascalCase.

**Why this is better:**

- **Consistent Syntax**: All prefixes use `@prefix/` notation; no mixing dots and colons
- **Import Once, Use Anywhere**: The import handles the prefix, component usage stays clean
- **Clear Ownership**: `@ui/` immediately signals this is from a prefixed folder

## What Stays the Same

All the great parts of JinjaX remain:

- **Component-based architecture** for organizing templates
- **Encapsulated CSS/JS** per component
- **The `attrs` object** for flexible attribute handling
- **Props with defaults** using `{#def name, title="Default" #}`
- **Content slots** for composability
- **Works great with htmx, Alpine.js, and TailwindCSS**


## The Bottom Line

Jx trades a small amount of upfront convenience (auto-discovery) for significant long-term benefits:

- **Clearer code** (explicit dependencies, no magic)
- **Easier debugging** (import errors vs runtime errors)
- **More flexibility** (especially for assets)
- **Familiar patterns** (imports work like Python, JavaScript, etc.)
- **Relative imports** (portability and encapsulation that JinjaX can't match)
- **Better tooling support** (navigation and refactoring)

If you're building anything beyond a toy project, these benefits compound quickly. Explicit imports make your codebase more maintainable, more understandable to new developers, and easier to refactor as it grows.

## Example: Real-World Comparison

**JinjaX approach:**
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

- Hard to tell where these components live
- No way to know if they exist until runtime
- Renaming `Components.User.ProfileCard` means finding all references manually
- Nested namespaces are verbose and repetitive

**Jx approach:**
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

- Clear dependencies listed at the top
- Clean component names without repetitive namespacing
- Import errors fail fast at load time

**Even better with relative imports:**

If your user components are organized in `components/user/`, you can make them more portable:

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

Now if you reorganize the user components, only this file's imports need updating; the internal dependencies between `ProfileCard` and `Avatar` remain intact.


## ⚡ Migration Guide

### Migrating Components

:::tip | Use the migration tool
The script [jx-migrate](https://github.com/jpsca/jx-migrate) can scan your folder of components, check what changes are needed, and do the migration automatically for you.

You are still going to do the migration of the Python code manually. [See the instructions below](#migrating-python-code).

Run `uvx https://raw.githubusercontent.com/jpsca/jx-migrate/main/migrate.py` and follow the instructions.
:::

If you prefer doing the component migration by hand, follow these steps.

#### Step 1: Add Imports

Go through each component and add explicit imports at the top:

```diff
+ {#import "components/card.jx" as Card #}
+ {#import "components/button.jx" as Button #}

  <Card>
    <Button>Click me</Button>
  </Card>
```

**Tip**: Use relative imports for components in the same folder or nearby:

```html+jinja
{# For siblings in the same folder #}
{#import "./sibling.jx" as Sibling #}

{# For components in a parent folder #}
{#import "../common/helper.jx" as Helper #}

{# For components in a subfolder #}
{#import "./parts/detail.jx" as Detail #}
```

This makes your components more portable and easier to reorganize.

#### Step 2: Replace Component References

Change dotted component names to imported names:

```diff
- <Common.UI.Card>
+ <Card>
```

#### Step 3: Update Asset Rendering

```diff
- {{ catalog.render_assets() }}
+ {{ assets.render() }}
```

Or use the more granular methods:

```html+jinja
{{ assets.render_css() }}
{{ assets.render_js(module=True) }}
```

#### Step 4: Update Named Slots (if used)

Replace `_slot` conditionals with `{% fill %}` blocks:

```diff
  {# Parent component #}
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

### Migrating Python code

After running the migration script, you need to update your Python integration code. Here's what changes for each framework.

#### 1. Replace the package

```bash
pip uninstall jinjax
pip install jx
```

#### 2. Update imports

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

#### 3. Update Catalog construction

JinjaX's `Catalog` takes all keyword arguments. Jx's `Catalog` accepts a positional `folder` shortcut and passes globals as `**kwargs`.

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

Key differences:
- `globals={"key": val}` dict → pass as `**kwargs` directly: `key=val`
- `root_url`, `file_ext`, `use_cache`, `fingerprint` → removed (Jx doesn't serve assets)
- `folder` → optional first positional argument (shortcut for `add_folder`)

#### 4. Update `render` calls

```python
# Before (JinjaX)
html = catalog.render("ComponentName", arg1="value", arg2=42)
# Component name used dot notation: "common.Form"

# After (Jx)
html = catalog.render("component-name.jx", arg1="value", arg2=42)
# Uses file path with extension: "common/form.jx"
```

Key differences:
- JinjaX uses PascalCase dot-notation component names: `"Card"`, `"common.Form"`
- Jx uses file paths with extension: `"card.jx"`, `"common/form.jx"`
- Jx also accepts a `globals` dict parameter for per-render globals:

```python
html = catalog.render(
    "page.jx",
    globals={"request": request, "csrf_token": token},
    title="Dashboard",
)
```

#### 5. Remove the middleware

JinjaX requires its own middleware to serve component CSS/JS. Jx doesn't — assets are just URLs served by your existing static file setup.

```python
# Before (JinjaX) — DELETE THIS
app.wsgi_app = catalog.get_middleware(app.wsgi_app)
```

Make sure your web framework's static file configuration serves the folder you chose during migration (the static folder) at the URL prefix you chose.

#### 6. Update special render parameters

```python
# Before (JinjaX)
html = catalog.render("Card", _content="<p>Hi</p>", _source="...", _globals={...})
# Also accepted legacy: __content, __source, __globals

# After (Jx) — these don't exist
# Use catalog.render_string() for inline source:
html = catalog.render_string("{#def name #}<p>{{ name }}</p>", name="Hi")
# Pass globals via the globals parameter:
html = catalog.render("card.jx", globals={"request": req}, title="Hi")
```

#### Framework-Specific Examples

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

##### Django (with django-jinja or manual Jinja2 setup)

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

#### Summary Checklist

- [ ] Install `jx` and uninstall `jinjax`
- [ ] `import jinjax` → `import jx`
- [ ] `jinjax.Catalog(...)` → `jx.Catalog(...)` with updated args
- [ ] `globals={...}` dict → `**kwargs`
- [ ] Remove `root_url`, `file_ext`, `use_cache`, `fingerprint` params
- [ ] `catalog.render("ComponentName", ...)` → `catalog.render("component-name.jx", ...)`
- [ ] Remove `catalog.get_middleware(...)` call
- [ ] Configure your static file server to serve the migrated assets
