import pydantic

from demo_openamp.datamodel.utils.util_pydantic import SchemaExtra


class ModelPidController(pydantic.BaseModel):
    name: str = pydantic.Field(
        default="AxisXYZ",
        json_schema_extra=SchemaExtra(
            comment="Name of the controlled axis",
        ).dict,
    )
    value: int = pydantic.Field(
        default=4095,
        ge=-4095,
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
