<!-- Autogenerated by reference.py -->

# Template tags


All following template tags are defined in

`django_components.templatetags.component_tags`

Import as
```django
{% load component_tags %}
```

## component_css_dependencies

```django
{% component_css_dependencies  %}
```



<a href="https://github.com/django-components/django-components/tree/master/src/django_components/templatetags/component_tags.py#L1024" target="_blank">See source code</a>



Marks location where CSS link tags should be rendered after the whole HTML has been generated.

Generally, this should be inserted into the `<head>` tag of the HTML.

If the generated HTML does NOT contain any `{% component_css_dependencies %}` tags, CSS links
are by default inserted into the `<head>` tag of the HTML. (See
[Default JS / CSS locations](../../concepts/advanced/rendering_js_css/#default-js-css-locations))

Note that there should be only one `{% component_css_dependencies %}` for the whole HTML document.
If you insert this tag multiple times, ALL CSS links will be duplicately inserted into ALL these places.

## component_js_dependencies

```django
{% component_js_dependencies  %}
```



<a href="https://github.com/django-components/django-components/tree/master/src/django_components/templatetags/component_tags.py#L1046" target="_blank">See source code</a>



Marks location where JS link tags should be rendered after the whole HTML has been generated.

Generally, this should be inserted at the end of the `<body>` tag of the HTML.

If the generated HTML does NOT contain any `{% component_js_dependencies %}` tags, JS scripts
are by default inserted at the end of the `<body>` tag of the HTML. (See
[Default JS / CSS locations](../../concepts/advanced/rendering_js_css/#default-js-css-locations))

Note that there should be only one `{% component_js_dependencies %}` for the whole HTML document.
If you insert this tag multiple times, ALL JS scripts will be duplicately inserted into ALL these places.

## component

```django
{% component *args: Any, **kwargs: Any [only] %}
{% endcomponent %}
```



<a href="https://github.com/django-components/django-components/tree/master/src/django_components/templatetags/component_tags.py#L2784" target="_blank">See source code</a>



Renders one of the components that was previously registered with
[`@register()`](./api.md#django_components.register)
decorator.

The `{% component %}` tag takes:

- Component's registered name as the first positional argument,
- Followed by any number of positional and keyword arguments.

```django
{% load component_tags %}
<div>
    {% component "button" name="John" job="Developer" / %}
</div>
```

The component name must be a string literal.

### Inserting slot fills

If the component defined any [slots](../concepts/fundamentals/slots.md), you can
"fill" these slots by placing the [`{% fill %}`](#fill) tags within the `{% component %}` tag:

```django
{% component "my_table" rows=rows headers=headers %}
  {% fill "pagination" %}
    < 1 | 2 | 3 >
  {% endfill %}
{% endcomponent %}
```

You can even nest [`{% fill %}`](#fill) tags within
[`{% if %}`](https://docs.djangoproject.com/en/5.2/ref/templates/builtins/#if),
[`{% for %}`](https://docs.djangoproject.com/en/5.2/ref/templates/builtins/#for)
and other tags:

```django
{% component "my_table" rows=rows headers=headers %}
    {% if rows %}
        {% fill "pagination" %}
            < 1 | 2 | 3 >
        {% endfill %}
    {% endif %}
{% endcomponent %}
```

### Isolating components

By default, components behave similarly to Django's
[`{% include %}`](https://docs.djangoproject.com/en/5.1/ref/templates/builtins/#include),
and the template inside the component has access to the variables defined in the outer template.

You can selectively isolate a component, using the `only` flag, so that the inner template
can access only the data that was explicitly passed to it:

```django
{% component "name" positional_arg keyword_arg=value ... only %}
```

Alternatively, you can set all components to be isolated by default, by setting
[`context_behavior`](../settings#django_components.app_settings.ComponentsSettings.context_behavior)
to `"isolated"` in your settings:

```python
# settings.py
COMPONENTS = {
    "context_behavior": "isolated",
}
```

### Omitting the `component` keyword

If you would like to omit the `component` keyword, and simply refer to your
components by their registered names:

```django
{% button name="John" job="Developer" / %}
```

You can do so by setting the "shorthand" [Tag formatter](../../concepts/advanced/tag_formatters)
in the settings:

```python
# settings.py
COMPONENTS = {
    "tag_formatter": "django_components.component_shorthand_formatter",
}
```

## fill

```django
{% fill name: str, *, data: Optional[str] = None, default: Optional[str] = None %}
{% endfill %}
```



<a href="https://github.com/django-components/django-components/tree/master/src/django_components/templatetags/component_tags.py#L648" target="_blank">See source code</a>



Use this tag to insert content into component's slots.

`{% fill %}` tag may be used only within a `{% component %}..{% endcomponent %}` block.
Runtime checks should prohibit other usages.

**Args:**

- `name` (str, required): Name of the slot to insert this content into. Use `"default"` for
    the default slot.
- `default` (str, optional): This argument allows you to access the original content of the slot
    under the specified variable name. See
    [Accessing original content of slots](../../concepts/fundamentals/slots#accessing-original-content-of-slots)
- `data` (str, optional): This argument allows you to access the data passed to the slot
    under the specified variable name. See [Scoped slots](../../concepts/fundamentals/slots#scoped-slots)

**Examples:**

Basic usage:
```django
{% component "my_table" %}
  {% fill "pagination" %}
    < 1 | 2 | 3 >
  {% endfill %}
{% endcomponent %}
```

### Accessing slot's default content with the `default` kwarg

```django
{# my_table.html #}
<table>
  ...
  {% slot "pagination" %}
    < 1 | 2 | 3 >
  {% endslot %}
</table>
```

```django
{% component "my_table" %}
  {% fill "pagination" default="default_pag" %}
    <div class="my-class">
      {{ default_pag }}
    </div>
  {% endfill %}
{% endcomponent %}
```

### Accessing slot's data with the `data` kwarg

```django
{# my_table.html #}
<table>
  ...
  {% slot "pagination" pages=pages %}
    < 1 | 2 | 3 >
  {% endslot %}
</table>
```

```django
{% component "my_table" %}
  {% fill "pagination" data="slot_data" %}
    {% for page in slot_data.pages %}
        <a href="{{ page.link }}">
          {{ page.index }}
        </a>
    {% endfor %}
  {% endfill %}
{% endcomponent %}
```

### Accessing slot data and default content on the default slot

To access slot data and the default slot content on the default slot,
use `{% fill %}` with `name` set to `"default"`:

```django
{% component "button" %}
  {% fill name="default" data="slot_data" default="default_slot" %}
    You clicked me {{ slot_data.count }} times!
    {{ default_slot }}
  {% endfill %}
{% endcomponent %}
```

## html_attrs

```django
{% html_attrs attrs: Optional[Dict] = None, defaults: Optional[Dict] = None, **kwargs: Any %}
```



<a href="https://github.com/django-components/django-components/tree/master/src/django_components/templatetags/component_tags.py#L18" target="_blank">See source code</a>



Generate HTML attributes (`key="value"`), combining data from multiple sources,
whether its template variables or static text.

It is designed to easily merge HTML attributes passed from outside with the internal.
See how to in [Passing HTML attributes to components](../../guides/howto/passing_html_attrs/).

**Args:**

- `attrs` (dict, optional): Optional dictionary that holds HTML attributes. On conflict, overrides
    values in the `default` dictionary.
- `default` (str, optional): Optional dictionary that holds HTML attributes. On conflict, is overriden
    with values in the `attrs` dictionary.
- Any extra kwargs will be appended to the corresponding keys

The attributes in `attrs` and `defaults` are merged and resulting dict is rendered as HTML attributes
(`key="value"`).

Extra kwargs (`key=value`) are concatenated to existing keys. So if we have

```python
attrs = {"class": "my-class"}
```

Then

```django
{% html_attrs attrs class="extra-class" %}
```

will result in `class="my-class extra-class"`.

**Example:**
```django
<div {% html_attrs
    attrs
    defaults:class="default-class"
    class="extra-class"
    data-id="123"
%}>
```

renders

```html
<div class="my-class extra-class" data-id="123">
```

**See more usage examples in
[HTML attributes](../../concepts/fundamentals/html_attributes#examples-for-html_attrs).**

## provide

```django
{% provide name: str, **kwargs: Any %}
{% endprovide %}
```



<a href="https://github.com/django-components/django-components/tree/master/src/django_components/templatetags/component_tags.py#L12" target="_blank">See source code</a>



The "provider" part of the [provide / inject feature](../../concepts/advanced/provide_inject).
Pass kwargs to this tag to define the provider's data.
Any components defined within the `{% provide %}..{% endprovide %}` tags will be able to access this data
with [`Component.inject()`](../api#django_components.Component.inject).

This is similar to React's [`ContextProvider`](https://react.dev/learn/passing-data-deeply-with-context),
or Vue's [`provide()`](https://vuejs.org/guide/components/provide-inject).

**Args:**

- `name` (str, required): Provider name. This is the name you will then use in
    [`Component.inject()`](../api#django_components.Component.inject).
- `**kwargs`: Any extra kwargs will be passed as the provided data.

**Example:**

Provide the "user_data" in parent component:

```python
@register("parent")
class Parent(Component):
    template = """
      <div>
        {% provide "user_data" user=user %}
          {% component "child" / %}
        {% endprovide %}
      </div>
    """

    def get_template_data(self, args, kwargs, slots, context):
        return {
            "user": kwargs["user"],
        }
```

Since the "child" component is used within the `{% provide %} / {% endprovide %}` tags,
we can request the "user_data" using `Component.inject("user_data")`:

```python
@register("child")
class Child(Component):
    template = """
      <div>
        User is: {{ user }}
      </div>
    """

    def get_template_data(self, args, kwargs, slots, context):
        user = self.inject("user_data").user
        return {
            "user": user,
        }
```

Notice that the keys defined on the `{% provide %}` tag are then accessed as attributes
when accessing them with [`Component.inject()`](../api#django_components.Component.inject).

✅ Do this
```python
user = self.inject("user_data").user
```

❌ Don't do this
```python
user = self.inject("user_data")["user"]
```

## slot

```django
{% slot name: str, **kwargs: Any [default] [required] %}
{% endslot %}
```



<a href="https://github.com/django-components/django-components/tree/master/src/django_components/templatetags/component_tags.py#L189" target="_blank">See source code</a>



Slot tag marks a place inside a component where content can be inserted
from outside.

[Learn more](../../concepts/fundamentals/slots) about using slots.

This is similar to slots as seen in
[Web components](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/slot),
[Vue](https://vuejs.org/guide/components/slots.html)
or [React's `children`](https://react.dev/learn/passing-props-to-a-component#passing-jsx-as-children).

**Args:**

- `name` (str, required): Registered name of the component to render
- `default`: Optional flag. If there is a default slot, you can pass the component slot content
    without using the [`{% fill %}`](#fill) tag. See
    [Default slot](../../concepts/fundamentals/slots#default-slot)
- `required`: Optional flag. Will raise an error if a slot is required but not given.
- `**kwargs`: Any extra kwargs will be passed as the slot data.

**Example:**

```python
@register("child")
class Child(Component):
    template = """
      <div>
        {% slot "content" default %}
          This is shown if not overriden!
        {% endslot %}
      </div>
      <aside>
        {% slot "sidebar" required / %}
      </aside>
    """
```

```python
@register("parent")
class Parent(Component):
    template = """
      <div>
        {% component "child" %}
          {% fill "content" %}
            🗞️📰
          {% endfill %}

          {% fill "sidebar" %}
            🍷🧉🍾
          {% endfill %}
        {% endcomponent %}
      </div>
    """
```

### Passing data to slots

Any extra kwargs will be considered as slot data, and will be accessible in the [`{% fill %}`](#fill)
tag via fill's `data` kwarg:

```python
@register("child")
class Child(Component):
    template = """
      <div>
        {# Passing data to the slot #}
        {% slot "content" user=user %}
          This is shown if not overriden!
        {% endslot %}
      </div>
    """
```

```python
@register("parent")
class Parent(Component):
    template = """
      {# Parent can access the slot data #}
      {% component "child" %}
        {% fill "content" data="data" %}
          <div class="wrapper-class">
            {{ data.user }}
          </div>
        {% endfill %}
      {% endcomponent %}
    """
```

### Accessing default slot content

The content between the `{% slot %}..{% endslot %}` tags is the default content that
will be rendered if no fill is given for the slot.

This default content can then be accessed from within the [`{% fill %}`](#fill) tag using
the fill's `default` kwarg.
This is useful if you need to wrap / prepend / append the original slot's content.

```python
@register("child")
class Child(Component):
    template = """
      <div>
        {% slot "content" %}
          This is default content!
        {% endslot %}
      </div>
    """
```

```python
@register("parent")
class Parent(Component):
    template = """
      {# Parent can access the slot's default content #}
      {% component "child" %}
        {% fill "content" default="default" %}
          {{ default }}
        {% endfill %}
      {% endcomponent %}
    """
```

