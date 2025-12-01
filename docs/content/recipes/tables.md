---
title: Table Components
description: Building data tables with sorting and actions
---

Tables are a great use case for components - define your structure once, reuse everywhere.

## Basic Table

```html+jinja title="components/table/table.jinja"
<table {{ attrs.render(class="table") }}>
  {{ content }}
</table>
```

```html+jinja title="components/table/thead.jinja"
<thead {{ attrs.render() }}>
  <tr>{{ content }}</tr>
</thead>
```

```html+jinja title="components/table/th.jinja"
<th {{ attrs.render() }}>{{ content }}</th>
```

```html+jinja title="components/table/tbody.jinja"
<tbody {{ attrs.render() }}>
  {{ content }}
</tbody>
```

```html+jinja title="components/table/tr.jinja"
<tr {{ attrs.render() }}>{{ content }}</tr>
```

```html+jinja title="components/table/td.jinja"
<td {{ attrs.render() }}>{{ content }}</td>
```

```html+jinja title="usage"
{#import "table/table.jinja" as Table #}
{#import "table/thead.jinja" as Thead #}
{#import "table/th.jinja" as Th #}
{#import "table/tbody.jinja" as Tbody #}
{#import "table/tr.jinja" as Tr #}
{#import "table/td.jinja" as Td #}

<Table class="table-striped">
  <Thead>
    <Th>Name</Th>
    <Th>Email</Th>
    <Th>Role</Th>
  </Thead>
  <Tbody>
    {% for user in users %}
      <Tr>
        <Td>{{ user.name }}</Td>
        <Td>{{ user.email }}</Td>
        <Td>{{ user.role }}</Td>
      </Tr>
    {% endfor %}
  </Tbody>
</Table>
```

## Data Table Component

A higher-level component that takes data directly:

```html+jinja title="components/data-table.jinja"
{#def columns, rows, empty_message="No data available" #}

<table {{ attrs.render(class="table") }}>
  <thead>
    <tr>
      {% for col in columns %}
        <th>{{ col.label if col is mapping else col }}</th>
      {% endfor %}
    </tr>
  </thead>
  <tbody>
    {% if rows %}
      {% for row in rows %}
        <tr>
          {% for col in columns %}
            {% set key = col.key if col is mapping else col %}
            <td>{{ row[key] if row is mapping else row[loop.index0] }}</td>
          {% endfor %}
        </tr>
      {% endfor %}
    {% else %}
      <tr>
        <td colspan="{{ columns | length }}" class="empty">
          {{ empty_message }}
        </td>
      </tr>
    {% endif %}
  </tbody>
</table>
```

```html+jinja title="usage"
{#import "data-table.jinja" as DataTable #}

<DataTable
  columns={{[
    {"key": "name", "label": "Name"},
    {"key": "email", "label": "Email"},
    {"key": "role", "label": "Role"},
  ]}}
  rows={{ users }}
/>
```

## Table with Actions

```html+jinja title="components/user-table.jinja"
{#import "./button.jinja" as Button #}
{#def users=[] #}

<table class="table">
  <thead>
    <tr>
      <th>Name</th>
      <th>Email</th>
      <th>Status</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {% for user in users %}
      <tr>
        <td>{{ user.name }}</td>
        <td>{{ user.email }}</td>
        <td>
          <span class="badge badge-{{ 'success' if user.active else 'secondary' }}">
            {{ "Active" if user.active else "Inactive" }}
          </span>
        </td>
        <td class="actions">
          <Button href="/users/{{ user.id }}/edit" size="sm">Edit</Button>
          <Button
            href="/users/{{ user.id }}/delete"
            size="sm"
            variant="danger"
            data-confirm="Are you sure?"
          >
            Delete
          </Button>
        </td>
      </tr>
    {% else %}
      <tr>
        <td colspan="4" class="empty">No users found</td>
      </tr>
    {% endfor %}
  </tbody>
</table>
```

## Sortable Headers

```html+jinja title="components/table/sortable-th.jinja"
{#def column, current_sort="", current_order="asc", base_url="" #}

{% set is_sorted = current_sort == column %}
{% set next_order = "desc" if is_sorted and current_order == "asc" else "asc" %}
{% set sort_url = base_url ~ "?sort=" ~ column ~ "&order=" ~ next_order %}

<th {{ attrs.render() }}>
  <a href="{{ sort_url }}" class="sortable {{ 'sorted-' ~ current_order if is_sorted else '' }}">
    {{ content }}
    {% if is_sorted %}
      <span class="sort-icon">{{ "▲" if current_order == "asc" else "▼" }}</span>
    {% endif %}
  </a>
</th>
```

```html+jinja title="usage"
{#import "table/sortable-th.jinja" as SortableTh #}
{#def users, sort="name", order="asc" #}

<table class="table">
  <thead>
    <tr>
      <SortableTh column="name" current_sort={{ sort }} current_order={{ order }} base_url="/users">
        Name
      </SortableTh>
      <SortableTh column="email" current_sort={{ sort }} current_order={{ order }} base_url="/users">
        Email
      </SortableTh>
      <SortableTh column="created_at" current_sort={{ sort }} current_order={{ order }} base_url="/users">
        Created
      </SortableTh>
    </tr>
  </thead>
  <tbody>
    {% for user in users %}
      <tr>
        <td>{{ user.name }}</td>
        <td>{{ user.email }}</td>
        <td>{{ user.created_at }}</td>
      </tr>
    {% endfor %}
  </tbody>
</table>
```

## Responsive Table

```html+jinja title="components/responsive-table.jinja"
{#css responsive-table.css #}

<div class="table-responsive">
  <table {{ attrs.render(class="table") }}>
    {{ content }}
  </table>
</div>
```

```css title="responsive-table.css"
.table-responsive {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
```

## Table with Row Selection

```html+jinja title="components/selectable-table.jinja"
{#def rows, id_key="id" #}
{#js selectable-table.js #}

<table class="table selectable-table" data-selectable>
  <thead>
    <tr>
      <th class="select-col">
        <input type="checkbox" data-select-all />
      </th>
      {{ content }}
    </tr>
  </thead>
  <tbody>
    {% for row in rows %}
      <tr data-row-id="{{ row[id_key] }}">
        <td class="select-col">
          <input type="checkbox" name="selected[]" value="{{ row[id_key] }}" />
        </td>
        {% slot row %}{% endslot %}
      </tr>
    {% endfor %}
  </tbody>
</table>
```

## Pagination Component

Pair with your tables:

```html+jinja title="components/pagination.jinja"
{#def page, total_pages, base_url #}

{% if total_pages > 1 %}
<nav class="pagination">
  {% if page > 1 %}
    <a href="{{ base_url }}?page={{ page - 1 }}" class="page-link">Previous</a>
  {% endif %}

  {% for p in range(1, total_pages + 1) %}
    {% if p == page %}
      <span class="page-link current">{{ p }}</span>
    {% else %}
      <a href="{{ base_url }}?page={{ p }}" class="page-link">{{ p }}</a>
    {% endif %}
  {% endfor %}

  {% if page < total_pages %}
    <a href="{{ base_url }}?page={{ page + 1 }}" class="page-link">Next</a>
  {% endif %}
</nav>
{% endif %}
```

```html+jinja title="usage"
{#import "user-table.jinja" as UserTable #}
{#import "pagination.jinja" as Pagination #}

<UserTable users={{ users }} />
<Pagination page={{ page }} total_pages={{ total_pages }} base_url="/users" />
```
