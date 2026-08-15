import pydantic
from utils.util_pydantic import SchemaExtra

from . import unittests_simple


class ModelSystemDual(pydantic.BaseModel):
    axis_x: unittests_simple.ModelPidController = pydantic.Field(
        default_factory=lambda :unittests_simple.ModelPidController(name="Axis X"),
    )
    axis_y: unittests_simple.ModelPidController = pydantic.Field(
        default_factory=lambda :unittests_simple.ModelPidController(name="Axis Y"),
    )
    debuglevel: int = pydantic.Field(
        default=4095,
        ge=0,
        le=4,
        json_schema_extra=SchemaExtra(
            unit="1",
            comment="0: off, 1: debug, 2: info, 3: warn, 4: error",
        ).dict,
    )

class ModelSystemList(pydantic.BaseModel):
    controllers: list[unittests_simple.ModelPidController] = pydantic.Field(
        min_length=2,
        max_length=2,
        default_factory=lambda: [
            unittests_simple.ModelPidController(name=name) for name in ["Axis R", "Axis S"]
        ],
    )
    debuglevel: int = pydantic.Field(
        default=4095,
        ge=0,
        le=4,
        json_schema_extra=SchemaExtra(
            unit="1",
            comment="0: off, 1: debug, 2: info, 3: warn, 4: error",
        ).dict,
    )

class ModelSystemDualList(pydantic.BaseModel):
    axis_x: unittests_simple.ModelPidController = pydantic.Field(
        default_factory=lambda :unittests_simple.ModelPidController(name="Axis X"),
    )
    axis_y: unittests_simple.ModelPidController = pydantic.Field(
        default_factory=lambda :unittests_simple.ModelPidController(name="Axis Y"),
    )
    debuglevel: int = pydantic.Field(
        default=4095,
        ge=0,
        le=4,
        json_schema_extra=SchemaExtra(
            unit="1",
            comment="0: off, 1: debug, 2: info, 3: warn, 4: error",
        ).dict,
    )
    controllers: list[unittests_simple.ModelPidController] = pydantic.Field(
        min_length=2,
        max_length=2,
        default_factory=lambda: [
            unittests_simple.ModelPidController(name=name) for name in ["Axis R", "Axis S"]
        ],
    )
