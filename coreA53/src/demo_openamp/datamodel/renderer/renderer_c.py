from __future__ import annotations

import ctypes
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel

from ..utils.util_pydantic import FieldInfoIter


@dataclass(frozen=True)
class TypeSourceC:
    """
    This is the mapping of the python datatype to the C code.
    """

    c_source: str
    """
    Example: "int32", "const char*", "float"
    """

    ctypes_type: type[ctypes._SimpleCData] | type[ctypes.Array]
    """
    ctypes....
    """

    to_ctypes: Callable[[object], object]
    from_ctypes: Callable[[object], object]

    @staticmethod
    def decode_c_string(value: object) -> str:
        if isinstance(value, bytes):
            return value.split(b"\0", 1)[0].decode("utf-8")
        return bytes(value).split(b"\0", 1)[0].decode("utf-8")

    @staticmethod
    def to_c_literal(value: object) -> str:
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

class TypeMapC(dict[type, TypeSourceC]):
    pass


TYPE_MAP_C = TypeMapC(
    {
        str: TypeSourceC(
            c_source="char {name}[32];",
            ctypes_type=ctypes.c_char * 32,
            to_ctypes=lambda value: value.encode("utf-8"),
            from_ctypes=TypeSourceC.decode_c_string,
        ),
        int: TypeSourceC(
            c_source="uint32_t {name};",
            ctypes_type=ctypes.c_uint32,
            to_ctypes=lambda value: ctypes.c_uint32(int(value)),
            from_ctypes=lambda value: int(value),
        ),
        float: TypeSourceC(
            c_source="double {name};",
            ctypes_type=ctypes.c_double,
            to_ctypes=lambda value: ctypes.c_double(float(value)),
            from_ctypes=lambda value: float(value),
        ),
    }
)



class RendererC:
    """Render a simple C struct definition from a Pydantic model."""

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.ctypes_model = self._create_ctypes_model()

    def render_c_struct(self) -> str:
        """
        Render 'self.model' into something like:

            typedef struct
            {
                char name[32];
                uint32_t value;
                double i_param;
            } ModelPidController_t;
        """
        lines = ["", "typedef struct", "{"]

        for field in FieldInfoIter.iter_model(self.model):
            annotation = field.field_info.annotation
            if annotation not in TYPE_MAP_C:
                raise ValueError(
                    f"Unsupported field type for '{field.field_name}': {annotation}"
                )

            comment = self._render_comment(field            )
            if comment:
                lines.append(f"    // {comment}")

            c_decl = TYPE_MAP_C[annotation].c_source.format(name=field.field_name)
            lines.append(f"    {c_decl}")

        struct_name = type(self.model).__name__
        lines.extend([f"}} {struct_name}_t;", ""])
        return "\n".join(lines)

    def render_c_initializer(self) -> str:
        struct_name = type(self.model).__name__
        var_name = self._model_var_name(struct_name)

        lines = ["", f"static const {struct_name}_t {var_name} = {{"]

        for field in FieldInfoIter.iter_model(self.model):
            if field.value_type not in TYPE_MAP_C:
                raise ValueError(
                    f"Unsupported field type for '{field.field_name}': {field.value_type_name}"
                )

            c_init_value = field.schema.get("CInitValue")
            if c_init_value is None:
                if field.field_info.is_required():
                    raise ValueError(
                        f"Field '{field.field_name}' is required and has no default/CInitValue"
                    )
                c_init_value = TypeSourceC.to_c_literal(field.get_value())

            lines.append(f"    {c_init_value},")

        if len(lines) > 2:
            lines[-1] = lines[-1].rstrip(",")

        lines.extend(["};", ""])
        return "\n".join(lines)

    def serialize_to_c(self, model: BaseModel) -> bytes:
        assert type(self.model) is type(model)
        instance = self.ctypes_model()
        for field in FieldInfoIter.iter_model(self.model):
            value = getattr(model, field.field_name)
            type_source = self._type_source_for_annotation(field.field_info.annotation)
            setattr(
                instance,
                field.field_name,
                type_source.to_ctypes(value),
            )

        return bytes(instance)

    def deserialize_from_c(self, serizalized: bytes) -> BaseModel:
        instance = self.ctypes_model.from_buffer_copy(serizalized)
        model_data = {}

        for field in FieldInfoIter.iter_model(self.model):
            raw_value = getattr(instance, field.field_name)
            type_source = self._type_source_for_annotation(field.field_info.annotation)
            model_data[field.field_name] = type_source.from_ctypes(raw_value)

        model_type = type(self.model)
        return model_type(**model_data)

    @staticmethod
    def _render_comment(field: FieldInfoIter) -> str:
        extra = field.schema_extra

        if extra.unit:
            return f"[{extra.unit}] {extra.comment}".strip()

        return extra.comment

    @staticmethod
    def _model_var_name(model_name: str) -> str:
        core_name = model_name[5:] if model_name.startswith("Model") else model_name
        chars: list[str] = []
        for index, char in enumerate(core_name):
            if char.isupper() and index > 0:
                chars.append("_")
            chars.append(char.lower())
        return "".join(chars)

    def _create_ctypes_model(self) -> type[ctypes.Structure]:
        """
        Create the ctypes structure matching the C layout of the model.
        """
        fields = []
        for field in FieldInfoIter.iter_model(self.model):
            annotation = field.field_info.annotation
            ctypes_type = self._type_source_for_annotation(annotation).ctypes_type
            fields.append((field.field_name, ctypes_type))

        class SerializedModel(ctypes.Structure):
            _fields_ = fields

        return SerializedModel

    @classmethod
    def _type_source_for_annotation(cls, annotation: object) -> TypeSourceC:
        if annotation not in TYPE_MAP_C:
            raise ValueError(f"Unsupported field type for serialization: {annotation}")
        return TYPE_MAP_C[annotation]
