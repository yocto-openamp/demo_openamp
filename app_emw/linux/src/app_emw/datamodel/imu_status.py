import pydantic
from utils.util_pydantic import SchemaExtra

PREFIX_M7 = "/m7"


class ModelImuStatus(pydantic.BaseModel):
    measurement_count: int = pydantic.Field(
        default=0,
        json_schema_extra=SchemaExtra(
            unit="[1]",
            comment="Count of measurements attempts",
        ).dict,
    )
    measurement_count_error: int = pydantic.Field(
        default=0,
        json_schema_extra=SchemaExtra(
            unit="[1]",
            comment="Count of failed measurements",
        ).dict,
    )
    accel_x: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="um/s^2",
            comment="Accel",
        ).dict,
    )
    accel_y: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="um/s^2",
            comment="Accel",
        ).dict,
    )
    accel_z: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="um/s^2",
            comment="Accel",
        ).dict,
    )
    gyro_x: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="urad/s",
            comment="Gyro",
        ).dict,
    )
    gyro_y: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="urad/s",
            comment="Gyro",
        ).dict,
    )
    gyro_z: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="urad/s",
            comment="Gyro",
        ).dict,
    )
