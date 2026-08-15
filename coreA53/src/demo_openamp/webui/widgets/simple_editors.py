from __future__ import annotations

import html
import logging
import typing

import annotated_types
import nicegui
import nicegui.binding
import nicegui.element
import nicegui.events
import pydantic_core
from nicegui import ui

from demo_openamp.datamodel.utils import util_observer
from demo_openamp.datamodel.utils.util_pydantic import FieldInfoIter

logger = logging.getLogger(__file__)

STYLE_QUALITY = "pl-4"
# PROPS_ENTRY = "borderless dense"
# PROPS_QUALITY = "value-color=blue"
PROPS_ENTRY = "outlined"
# STYLE_ENTRY = "p-0"  # "flex-1 min-h-0 p-0"
STYLE_ENTRY = "w-1/2"  # 50% of the page width. It would be better to use: Quasar row grid, use a row parent and col-6 classes.


def bind_quality_bg_color(
    element: nicegui.element.Element,
    observable: util_observer.ObservableItem,
) -> None:
    quality_bg_colors: dict[util_observer.EnumItemQuality, str] = {
        util_observer.EnumItemQuality.UNKNOWN: "grey-4",
        util_observer.EnumItemQuality.KNOWN: "green-1",
        util_observer.EnumItemQuality.IN_TRANSITION: "orange-1",
    }
    nicegui.binding.bind_from(
        element._props,
        "bg-color",
        observable,
        "quality",
        backward=lambda quality: quality_bg_colors.get(quality, "grey-3"),
        self_strict=False,
    )


def create_quality_label(observable: util_observer.ObservableItem) -> None:
    quality_colors: dict[util_observer.EnumItemQuality, str] = {
        util_observer.EnumItemQuality.UNKNOWN: "var(--q-grey-6)",
        util_observer.EnumItemQuality.KNOWN: "var(--q-positive)",
        util_observer.EnumItemQuality.IN_TRANSITION: "var(--q-warning)",
    }

    (
        ui.html(content="...")
        .classes(STYLE_QUALITY)
        .bind_content_from(
            observable,
            "quality",
            backward=lambda quality: (
                f'<span style="color: {quality_colors.get(quality, "var(--q-grey-6)")}">'
                f"{observable.path}<br/>quality: {html.escape(quality.value)}</span>"
            ),
        )
    )


async def set_and_validate(
    observer: util_observer.Observer,
    path: str,
    field: FieldInfoIter,
    event: nicegui.events.UiEventArguments,
) -> None:
    assert isinstance(path, str)
    assert isinstance(field, FieldInfoIter)
    assert isinstance(event, nicegui.events.UiEventArguments)
    if isinstance(event, nicegui.events.ValueChangeEventArguments):
        value = event.value
        try:
            field.set_value(value)
        except pydantic_core.ValidationError as e:
            msg = e.errors()[0]["msg"]
            event.sender.error = msg
            logger.warning(f"{path}: {msg}")

        await observer.set_request(path=path, value=value)

    pass


def create_text_field(
    observer: util_observer.Observer,
    path: str,
    field: FieldInfoIter,
) -> None:
    observable = observer.get_item(path=path)
    unit = field.schema_extra.unit

    value = field.get_value()

    input_element = (
        ui.input(
            label=field.title,
            value=value,
            suffix=unit,
            on_change=lambda event: set_and_validate(
                observer=observer,
                path=path,
                field=field,
                event=event,
            ),
        )
        .props(PROPS_ENTRY)
        .props(f'hint="{field.schema_extra.comment}"')
        .classes(STYLE_ENTRY)
        .bind_value(observable, "value")
    )
    bind_quality_bg_color(element=input_element, observable=observable)
    create_quality_label(observable=observable)


def create_integer_field(
    observer: util_observer.Observer,
    path: str,
    field: FieldInfoIter,
) -> None:
    observable = observer.get_item(path=path)
    unit = field.schema_extra.unit

    value = field.get_value()
    number_element = (
        ui.number(
            label=field.title,
            value=value,
            min=field.get_annotation(annotated_types.Ge).ge,
            max=field.get_annotation(annotated_types.Le).le,
            step=1,
            suffix=unit,
            on_change=lambda event: set_and_validate(
                observer=observer,
                path=path,
                field=field,
                event=event,
            ),
        )
        .props(PROPS_ENTRY)
        .props(f'hint="{field.schema_extra.comment}"')
        .classes(STYLE_ENTRY)
        .bind_value(observable, "value")
    )
    bind_quality_bg_color(element=number_element, observable=observable)

    create_quality_label(observable=observable)


def create_slider_field(
    observer: util_observer.Observer,
    path: str,
    field: FieldInfoIter,
) -> None:
    observable = observer.get_item(path=path)

    ui.label(field.title).classes("min-w-24 font-medium leading-none p-0")

    value = field.get_value()
    slider_element = (
        ui.slider(
            value=value,
            min=field.get_annotation(annotated_types.Ge).ge,
            max=field.get_annotation(annotated_types.Le).le,
            step=1,
            on_change=lambda event: set_and_validate(
                observer=observer,
                path=path,
                field=field,
                event=event,
            ),
        )
        .props(PROPS_ENTRY)
        .props(f'hint="{field.schema_extra.comment}"')
        .classes(STYLE_ENTRY)
        .bind_value(observable, "value")
    )
    bind_quality_bg_color(element=slider_element, observable=observable)

    create_quality_label(observable=observable)


def create_selection_field(
    observer: util_observer.Observer,
    path: str,
    field: FieldInfoIter,
    options: list | dict,
) -> None:
    observable = observer.get_item(path=path)

    value = field.get_value()
    select_element = (
        ui.select(
            label=field.title,
            options=options,
            value=value,
            on_change=lambda event: set_and_validate(
                observer=observer,
                path=path,
                field=field,
                event=event,
            ),
        )
        .props(PROPS_ENTRY)
        .props(f'hint="{field.schema_extra.comment}"')
        .classes(STYLE_ENTRY)
        .bind_value(observable, "value")
    )
    bind_quality_bg_color(element=select_element, observable=observable)

    create_quality_label(observable=observable)


def create_float_field(
    observer: util_observer.Observer,
    path: str,
    field: FieldInfoIter,
) -> None:
    observable = observer.get_item(path=path)
    unit = field.schema_extra.unit

    value = field.get_value()

    number_element = (
        ui.number(
            label=field.title,
            value=value,
            min=field.schema.get("minimum"),
            max=field.schema.get("maximum"),
            step=0.1,
            suffix=unit,
            on_change=lambda event: set_and_validate(
                observer=observer,
                path=path,
                field=field,
                event=event,
            ),
        )
        .props(PROPS_ENTRY)
        .props(f'hint="{field.schema_extra.comment}"')
        .classes(STYLE_ENTRY)
        .bind_value(observable, "value")
    )
    bind_quality_bg_color(element=number_element, observable=observable)
    create_quality_label(observable=observable)


class TypeMapNiceGUI(
    dict[
        type,
        typing.Callable[
            [util_observer.Observer, str, FieldInfoIter],
            None,
        ],
    ]
):
    pass


TYPE_MAP_NICE_GUI = TypeMapNiceGUI(
    {
        str: create_text_field,
        int: create_integer_field,
        float: create_float_field,
    }
)
