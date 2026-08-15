from __future__ import annotations

import dataclasses
import logging
import typing

import annotated_types
import pydantic

logger = logging.getLogger(__file__)


@dataclasses.dataclass(frozen=True)
class FieldInfoIter:
    model: pydantic.BaseModel
    field_name: str
    field_info: pydantic.fields.FieldInfo

    @property
    def is_list(self) -> bool:
        return self.value_type_name == "list"

    @property
    def schema(self) -> dict[str, typing.Any]:
        assert isinstance(self.field_info.json_schema_extra, dict)
        return self.field_info.json_schema_extra

    @property
    def title(self) -> str:
        return self.field_info.title or self.field_name.replace("_", " ").title()

    @property
    def value_type(self) -> type[typing.Any]:
        assert self.field_info.annotation is not None
        return self.field_info.annotation

    @property
    def value_type_name(self) -> str:
        return self.value_type.__name__

    @property
    def schema_extra(self) -> SchemaExtra:
        try:
            if self.field_info.json_schema_extra is None:
                return SchemaExtra()
            assert isinstance(self.field_info.json_schema_extra, dict)
            extra = SchemaExtra(**self.field_info.json_schema_extra)
            return extra
        except Exception as e:
            logger.error(f"Field '{self.field_name}': {e}!")
            return SchemaExtra()

    def get_annotation[T: annotated_types.BaseMetadata](
        self,
        annotated_type: type[T],
    ) -> T:
        for j in self.field_info.metadata:
            if isinstance(j, annotated_type):
                return j
        raise NotImplementedError()

    def get_value(self) -> typing.Any:
        return getattr(self.model, self.field_name)

    def set_value(self, value: typing.Any) -> None:
        setattr(self.model, self.field_name, value)

    def get_default_value(self) -> typing.Any:
        return self.field_info.default

    @staticmethod
    def iter_model(model: pydantic.BaseModel) -> typing.Iterator[FieldInfoIter]:
        assert isinstance(model, pydantic.BaseModel)
        for field_name, field_info in type(model).model_fields.items():
            yield FieldInfoIter(
                model=model, field_name=field_name, field_info=field_info
            )


@dataclasses.dataclass(frozen=True)
class SchemaExtra:
    unit: str = ""
    """
    Examples: m, V, step
    """

    comment: str = ""
    """
    Examples: Encoder steps
    """

    title_lookup: str | None = None

    @property
    def dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class FieldHierarchy:
    path: str
    field: FieldInfoIter

    @property
    def default_value(self) -> typing.Any:
        return self.field.field_info.default

    @property
    def value(self) -> typing.Any:
        return self.field.get_value()


@dataclasses.dataclass(frozen=True)
class ModelHierarchy:
    prefix: str
    model: pydantic.BaseModel
    field: FieldInfoIter | None
    parent: ModelHierarchy | None
    compounds: dict[str, ModelHierarchy] = dataclasses.field(default_factory=dict)
    """
    /first
    /second
    /controllers/0
    /controllers/1
    """
    elements: dict[str, FieldInfoIter] = dataclasses.field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        assert isinstance(self.prefix, str)
        assert self.prefix.startswith("/")
        assert isinstance(self.model, pydantic.BaseModel)
        assert isinstance(self.field, FieldInfoIter | None)
        assert isinstance(self.parent, ModelHierarchy | None)
        for v in self.elements.keys():
            assert isinstance(v, str)
        for v in self.elements.values():
            assert isinstance(v, FieldInfoIter)
        for v in self.compounds.keys():
            assert isinstance(v, str)
        for v in self.compounds.values():
            assert isinstance(v, ModelHierarchy)

    @staticmethod
    def factory(
        model: pydantic.BaseModel,
        prefix: str = "/",
        parent: ModelHierarchy | None = None,
        field: FieldInfoIter | None = None,
    ) -> ModelHierarchy:
        assert isinstance(model, pydantic.BaseModel)
        assert isinstance(prefix, str)
        assert isinstance(parent, ModelHierarchy | None)
        assert prefix.startswith("/")

        mh = ModelHierarchy(prefix=prefix, parent=parent, field=field, model=model)

        for field in FieldInfoIter.iter_model(model):
            if prefix == "/":
                path = f"/{field.field_name}"
            else:
                path = f"{prefix}/{field.field_name}"
            child_model = getattr(model, field.field_name)

            # annotation = field.field_info.annotation
            # if (annotation is list) or (typing.get_origin(annotation) is list):
            if isinstance(child_model, list):
                min_length = field.get_annotation(annotated_types.MinLen).min_length
                max_length = field.get_annotation(annotated_types.MaxLen).max_length
                assert min_length == max_length
                assert len(child_model) == min_length

                for i, _child_model in enumerate(child_model):
                    prefix = f"{path}/{i}"
                    _child_field = FieldInfoIter(
                        model=_child_model,
                        field_name=field.field_name,
                        field_info=field.field_info,
                    )
                    mh.compounds[prefix] = ModelHierarchy.factory(
                        prefix=prefix,
                        parent=mh,
                        field=_child_field,
                        model=_child_model,
                    )
                continue

            if isinstance(child_model, pydantic.BaseModel):
                mh.compounds[path] = ModelHierarchy.factory(
                    parent=mh,
                    prefix=path,
                    field=field,
                    model=child_model,
                )
                continue

            mh.elements[path] = field

        return mh

    def get_by_path(self, path: str) -> FieldHierarchy:
        for element in self.iter_elements:
            if element.path == path:
                return element

        raise ValueError(f"Path not found in '{self.class_name}': {path}")

    @property
    def title(self) -> str:
        if self.field is None:
            return "?"
        title_lookup = self.field.schema_extra.title_lookup
        if title_lookup:
            try:
                return getattr(self.model, title_lookup)
            except AttributeError:
                logger.error(
                    f"Failed to read property title_lookup='{title_lookup}' in {self.class_name}"
                )
                return self.class_name

        return self.field.title

    @property
    def class_name(self) -> str:
        return self.model.__class__.__name__

    @property
    def all_elements(self) -> list[FieldHierarchy]:
        return list(self.iter_elements)

    @property
    def iter_elements(self) -> typing.Iterator[FieldHierarchy]:
        for path, item in self.elements.items():
            yield FieldHierarchy(path=path, field=item)
        for _path, item in self.compounds.items():
            yield from item.iter_elements

    def dump(self):
        for path, item in self.compounds.items():
            print(f"compound: {path} - {item.class_name}")
            item.dump()
        for path, item in self.elements.items():
            print(f"element:  {path} - {item.value_type_name}")
