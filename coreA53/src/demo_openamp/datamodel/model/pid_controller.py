import pydantic

from ..utils.util_pydantic import SchemaExtra


class ModelPidController(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    names: str = pydantic.Field(
        default="AxisXYZ",
        min_length=3,
        max_length=20,
        json_schema_extra=SchemaExtra(
            comment="Name of the controlled axis",
        ).dict,
    )
    value: int = pydantic.Field(
        default=4095,
        ge=-4096,
        le=4095,
        json_schema_extra=SchemaExtra(
            unit="steps (4096 steps = 1 revolution)",
            comment="Encoder steps",
        ).dict,
    )
    i_param: float = pydantic.Field(
        default=0.25,
        json_schema_extra=SchemaExtra(
            unit="s",
            comment="Integral gain (I) of the PID controller",
        ).dict,
    )


class ModelCommon(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    debuglevel: int = pydantic.Field(
        default=3,
        ge=0,
        le=4,
        json_schema_extra=SchemaExtra(
            comment="0: off, 1: debug, 2: info, 3: warn, 4: error",
        ).dict,
    )


class ModelSystemDual(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    common: ModelCommon = pydantic.Field(
        default_factory=lambda: ModelCommon(),
    )
    axis_x: ModelPidController = pydantic.Field(
        default_factory=lambda: ModelPidController(name="Axis X"),
    )
    axis_y: ModelPidController = pydantic.Field(
        default_factory=lambda: ModelPidController(name="Axis Y"),
    )
    axis_z: ModelPidController = pydantic.Field(
        default_factory=lambda: ModelPidController(name="Axis Z"),
    )
    controllers: list[ModelPidController] = pydantic.Field(
        min_length=2,
        max_length=2,
        default_factory=lambda: [
            ModelPidController(name=name) for name in ["Axis R", "Axis S"]
        ],
        json_schema_extra=SchemaExtra(
            title_lookup="name",
        ).dict,
    )


