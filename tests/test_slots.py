"""
Tests focusing on the Python part of slots.
For tests focusing on the `{% slot %}` tag, see `test_templatetags_slot_fill.py`
"""

import re

import pytest
from django.template import Context, Template, TemplateSyntaxError
from django.template.base import NodeList, TextNode
from pytest_django.asserts import assertHTMLEqual

from django_components import Component, register, types
from django_components.slots import Slot, SlotContext, SlotFallback

from django_components.testing import djc_test
from .testutils import PARAMETRIZE_CONTEXT_BEHAVIOR, setup_test_config

setup_test_config({"autodiscover": False})


# Test interaction of the `Slot` instances with Component rendering
@djc_test
class TestSlot:
    @djc_test(
        parametrize=(
            ["components_settings", "is_isolated"],
            [
                [{"context_behavior": "django"}, False],
                [{"context_behavior": "isolated"}, True],
            ],
            ["django", "isolated"],
        )
    )
    def test_render_slot_as_func(self, components_settings, is_isolated):
        class SimpleComponent(Component):
            template: types.django_html = """
                {% load component_tags %}
                {% slot "first" required data1="abc" data2:hello="world" data2:one=123 %}
                    SLOT_DEFAULT
                {% endslot %}
            """

            def get_template_data(self, args, kwargs, slots, context):
                return {
                    "the_arg": args[0],
                    "the_kwarg": kwargs.pop("the_kwarg", None),
                    "kwargs": kwargs,
                }

        def slot_fn(ctx: SlotContext):
            context = ctx.context
            assert isinstance(context, Context)
            # NOTE: Since the slot has access to the Context object, it should behave
            # the same way as it does in templates - when in "isolated" mode, then the
            # slot fill has access only to the "root" context, but not to the data of
            # get_template_data() of SimpleComponent.
            if is_isolated:
                assert context.get("the_arg") is None
                assert context.get("the_kwarg") is None
                assert context.get("kwargs") is None
                assert context.get("abc") is None
            else:
                assert context["the_arg"] == "1"
                assert context["the_kwarg"] == 3
                assert context["kwargs"] == {}
                assert context["abc"] == "def"

            slot_data_expected = {
                "data1": "abc",
                "data2": {"hello": "world", "one": 123},
            }
            assert slot_data_expected == ctx.data

            assert isinstance(ctx.fallback, SlotFallback)
            assert "SLOT_DEFAULT" == str(ctx.fallback).strip()

            return f"FROM_INSIDE_SLOT_FN | {ctx.fallback}"

        rendered = SimpleComponent.render(
            context={"abc": "def"},
            args=["1"],
            kwargs={"the_kwarg": 3},
            slots={"first": slot_fn},
        )
        assertHTMLEqual(
            rendered,
            "FROM_INSIDE_SLOT_FN | SLOT_DEFAULT",
        )

    @djc_test(parametrize=PARAMETRIZE_CONTEXT_BEHAVIOR)
    def test_render_raises_on_missing_slot(self, components_settings):
        class SimpleComponent(Component):
            template: types.django_html = """
                {% load component_tags %}
                {% slot "first" required %}
                {% endslot %}
            """

        with pytest.raises(
            TemplateSyntaxError,
            match=re.escape("Slot 'first' is marked as 'required' (i.e. non-optional), yet no fill is provided."),
        ):
            SimpleComponent.render()

        with pytest.raises(
            TemplateSyntaxError,
            match=re.escape("Slot 'first' is marked as 'required' (i.e. non-optional), yet no fill is provided."),
        ):
            SimpleComponent.render(
                slots={"first": None},
            )

        SimpleComponent.render(
            slots={"first": "SLOT_FN"},
        )

    def test_render_slot_in_python__minimal(self):
        def slot_fn(ctx: SlotContext):
            assert ctx.context is None
            assert ctx.data == {}
            assert ctx.fallback is None

            return "FROM_INSIDE_SLOT_FN"

        slot: Slot = Slot(slot_fn)
        rendered = slot()
        assertHTMLEqual(
            rendered,
            "FROM_INSIDE_SLOT_FN",
        )

    def test_render_slot_in_python__with_data(self):
        def slot_fn(ctx: SlotContext):
            assert ctx.context is not None
            assert ctx.context["the_arg"] == "1"
            assert ctx.context["the_kwarg"] == 3
            assert ctx.context["kwargs"] == {}
            assert ctx.context["abc"] == "def"

            slot_data_expected = {
                "data1": "abc",
                "data2": {"hello": "world", "one": 123},
            }
            assert slot_data_expected == ctx.data

            assert isinstance(ctx.fallback, str)
            assert "SLOT_DEFAULT" == ctx.fallback

            return f"FROM_INSIDE_SLOT_FN | {ctx.fallback}"

        slot: Slot = Slot(slot_fn)
        context = Context({"the_arg": "1", "the_kwarg": 3, "kwargs": {}, "abc": "def"})

        # Test positional arguments
        rendered = slot(
            {"data1": "abc", "data2": {"hello": "world", "one": 123}},
            "SLOT_DEFAULT",
            context,
        )
        assertHTMLEqual(
            rendered,
            "FROM_INSIDE_SLOT_FN | SLOT_DEFAULT",
        )

        # Test keyword arguments
        rendered2 = slot(
            data={"data1": "abc", "data2": {"hello": "world", "one": 123}},
            fallback="SLOT_DEFAULT",
            context=context,
        )
        assertHTMLEqual(
            rendered2,
            "FROM_INSIDE_SLOT_FN | SLOT_DEFAULT",
        )

    # Part of the slot caching feature - test that static content slots reuse the slot function.
    # See https://github.com/django-components/django-components/issues/1164#issuecomment-2854682354
    def test_slots_reuse_functions__string(self):
        captured_slots = {}

        class SimpleComponent(Component):
            template: types.django_html = """
                {% load component_tags %}
                {% slot "first" required %}
                {% endslot %}
            """

            def get_template_data(self, args, kwargs, slots, context):
                nonlocal captured_slots
                captured_slots = slots

        SimpleComponent.render(
            slots={"first": "FIRST_SLOT"},
        )

        first_slot_func = captured_slots["first"]
        first_nodelist: NodeList = first_slot_func.nodelist
        assert isinstance(first_slot_func, Slot)
        assert first_slot_func.content_func is not None
        assert first_slot_func.contents == "FIRST_SLOT"
        assert len(first_nodelist) == 1
        assert isinstance(first_nodelist[0], TextNode)
        assert first_nodelist[0].s == "FIRST_SLOT"

        captured_slots = {}
        SimpleComponent.render(
            slots={"first": "FIRST_SLOT"},
        )

        second_slot_func = captured_slots["first"]
        second_nodelist: NodeList = second_slot_func.nodelist
        assert isinstance(second_slot_func, Slot)
        assert second_slot_func.content_func is not None
        assert second_slot_func.contents == "FIRST_SLOT"
        assert len(second_nodelist) == 1
        assert isinstance(second_nodelist[0], TextNode)
        assert second_nodelist[0].s == "FIRST_SLOT"

        assert first_slot_func.contents == second_slot_func.contents

    # Part of the slot caching feature - test that consistent functions passed as slots
    # reuse the slot function.
    def test_slots_reuse_functions__func(self):
        captured_slots = {}

        class SimpleComponent(Component):
            template: types.django_html = """
                {% load component_tags %}
                {% slot "first" required %}
                {% endslot %}
            """

            def get_template_data(self, args, kwargs, slots, context):
                nonlocal captured_slots
                captured_slots = slots

        slot_func = lambda ctx: "FROM_INSIDE_SLOT"  # noqa: E731

        SimpleComponent.render(
            slots={"first": slot_func},
        )

        first_slot_func = captured_slots["first"]
        assert isinstance(first_slot_func, Slot)
        assert callable(first_slot_func.content_func)
        assert callable(first_slot_func.contents)
        assert first_slot_func.nodelist is None

        captured_slots = {}
        SimpleComponent.render(
            slots={"first": slot_func},
        )

        second_slot_func = captured_slots["first"]
        assert isinstance(second_slot_func, Slot)
        assert callable(second_slot_func.content_func)
        assert callable(second_slot_func.contents)
        assert second_slot_func.nodelist is None

        # NOTE: Both are functions, but different, because internally we wrap the function
        #       to escape the results.
        assert first_slot_func.contents is not second_slot_func.contents

    # Part of the slot caching feature - test that `Slot` instances with identical function
    # passed as slots reuse the slot function.
    def test_slots_reuse_functions__slot(self):
        captured_slots = {}

        class SimpleComponent(Component):
            template: types.django_html = """
                {% load component_tags %}
                {% slot "first" required %}
                {% endslot %}
            """

            def get_template_data(self, args, kwargs, slots, context):
                nonlocal captured_slots
                captured_slots = slots

        slot_func = lambda ctx: "FROM_INSIDE_SLOT"  # noqa: E731

        SimpleComponent.render(
            slots={"first": Slot(slot_func)},
        )

        first_slot_func = captured_slots["first"]
        assert isinstance(first_slot_func, Slot)
        assert callable(first_slot_func.content_func)
        assert callable(first_slot_func.contents)
        assert first_slot_func.nodelist is None

        captured_slots = {}
        SimpleComponent.render(
            slots={"first": Slot(slot_func)},
        )

        second_slot_func = captured_slots["first"]
        assert isinstance(second_slot_func, Slot)
        assert callable(second_slot_func.content_func)
        assert callable(second_slot_func.contents)
        assert second_slot_func.nodelist is None

        assert first_slot_func.contents == second_slot_func.contents

    # Part of the slot caching feature - test that identical slot fill content
    # slots reuse the slot function.
    def test_slots_reuse_functions__fill_tag_default(self):
        captured_slots = {}

        @register("test")
        class SimpleComponent(Component):
            template: types.django_html = """
                {% load component_tags %}
                {% slot "first" default %}
                {% endslot %}
            """

            def get_template_data(self, args, kwargs, slots, context):
                nonlocal captured_slots
                captured_slots = slots

        template_str: types.django_html = """
            {% load component_tags %}
            {% component "test" %}
              FROM_INSIDE_DEFAULT_SLOT
            {% endcomponent %}
        """
        template = Template(template_str)

        template.render(Context())

        first_slot_func = captured_slots["default"]
        first_nodelist: NodeList = first_slot_func.nodelist
        assert isinstance(first_slot_func, Slot)
        assert callable(first_slot_func.content_func)
        assert first_slot_func.contents == "\n              FROM_INSIDE_DEFAULT_SLOT\n            "
        assert len(first_nodelist) == 1
        assert isinstance(first_nodelist[0], TextNode)
        assert first_nodelist[0].s == "\n              FROM_INSIDE_DEFAULT_SLOT\n            "

        captured_slots = {}
        template.render(Context())

        second_slot_func = captured_slots["default"]
        second_nodelist: NodeList = second_slot_func.nodelist
        assert isinstance(second_slot_func, Slot)
        assert callable(second_slot_func.content_func)
        assert second_slot_func.contents == "\n              FROM_INSIDE_DEFAULT_SLOT\n            "
        assert len(second_nodelist) == 1
        assert isinstance(second_nodelist[0], TextNode)
        assert second_nodelist[0].s == "\n              FROM_INSIDE_DEFAULT_SLOT\n            "

        assert first_slot_func.contents == second_slot_func.contents

    # Part of the slot caching feature - test that identical slot fill content
    # slots reuse the slot function.
    def test_slots_reuse_functions__fill_tag_named(self):
        captured_slots = {}

        @register("test")
        class SimpleComponent(Component):
            template: types.django_html = """
                {% load component_tags %}
                {% slot "first" default %}
                {% endslot %}
            """

            def get_template_data(self, args, kwargs, slots, context):
                nonlocal captured_slots
                captured_slots = slots

        template_str: types.django_html = """
            {% load component_tags %}
            {% component "test" %}
              {% fill "first" %}
                FROM_INSIDE_NAMED_SLOT
              {% endfill %}
            {% endcomponent %}
        """
        template = Template(template_str)

        template.render(Context())

        first_slot_func = captured_slots["first"]
        first_nodelist: NodeList = first_slot_func.nodelist
        assert isinstance(first_slot_func, Slot)
        assert callable(first_slot_func.content_func)
        assert first_slot_func.contents == "\n                FROM_INSIDE_NAMED_SLOT\n              "
        assert len(first_nodelist) == 1
        assert isinstance(first_nodelist[0], TextNode)
        assert first_nodelist[0].s == "\n                FROM_INSIDE_NAMED_SLOT\n              "

        captured_slots = {}
        template.render(Context())

        second_slot_func = captured_slots["first"]
        second_nodelist: NodeList = second_slot_func.nodelist
        assert isinstance(second_slot_func, Slot)
        assert callable(second_slot_func.content_func)
        assert second_slot_func.contents == "\n                FROM_INSIDE_NAMED_SLOT\n              "
        assert len(second_nodelist) == 1
        assert isinstance(second_nodelist[0], TextNode)
        assert second_nodelist[0].s == "\n                FROM_INSIDE_NAMED_SLOT\n              "

        assert first_slot_func.contents == second_slot_func.contents

    def test_pass_body_to_fill__slot(self):
        @register("test")
        class SimpleComponent(Component):
            template: types.django_html = """
                {% load component_tags %}
                {% slot "first" default %}
                {% endslot %}
            """

        template_str: types.django_html = """
            {% load component_tags %}
            {% component "test" %}
              {% fill "first" body=my_slot / %}
            {% endcomponent %}
        """
        template = Template(template_str)

        my_slot: Slot = Slot(lambda ctx: "FROM_INSIDE_NAMED_SLOT")
        rendered: str = template.render(Context({"my_slot": my_slot}))

        assert rendered.strip() == "FROM_INSIDE_NAMED_SLOT"

    def test_pass_body_to_fill__string(self):
        @register("test")
        class SimpleComponent(Component):
            template: types.django_html = """
                {% load component_tags %}
                {% slot "first" default %}
                {% endslot %}
            """

        template_str: types.django_html = """
            {% load component_tags %}
            {% component "test" %}
              {% fill "first" body=my_slot / %}
            {% endcomponent %}
        """
        template = Template(template_str)

        rendered: str = template.render(Context({"my_slot": "FROM_INSIDE_NAMED_SLOT"}))

        assert rendered.strip() == "FROM_INSIDE_NAMED_SLOT"

    def test_pass_body_to_fill_raises_on_body(self):
        @register("test")
        class SimpleComponent(Component):
            template: types.django_html = """
                {% load component_tags %}
                {% slot "first" default %}
                {% endslot %}
            """

        template_str: types.django_html = """
            {% load component_tags %}
            {% component "test" %}
              {% fill "first" body=my_slot %}
                FROM_INSIDE_NAMED_SLOT
              {% endfill %}
            {% endcomponent %}
        """
        template = Template(template_str)

        my_slot: Slot = Slot(lambda ctx: "FROM_INSIDE_NAMED_SLOT")

        with pytest.raises(
            TemplateSyntaxError,
            match=re.escape("Fill 'first' received content both through 'body' kwarg and '{% fill %}' body."),
        ):
            template.render(Context({"my_slot": my_slot}))
