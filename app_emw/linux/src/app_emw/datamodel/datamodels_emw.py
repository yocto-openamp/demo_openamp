import pydantic
from experiment_datadefinitions.utils.util_pydantic import SchemaExtra


class ModelImuStatus(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    measurement_count: int = pydantic.Field(
        default=0,
        ge=0,
        le=2**32 - 1,
        json_schema_extra=SchemaExtra(
            unit="[1]",
            comment="Count of measurements attempts",
        ).dict,
    )
    measurement_count_error: int = pydantic.Field(
        default=0,
        ge=0,
        le=2**32 - 1,
        json_schema_extra=SchemaExtra(
            unit="[1]",
            comment="Count of failed measurements",
        ).dict,
    )
    accel_x: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="m/s^2",
            comment="Accel",
        ).dict,
    )
    accel_y: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="m/s^2",
            comment="Accel",
        ).dict,
    )
    accel_z: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="m/s^2",
            comment="Accel",
        ).dict,
    )
    gyro_x: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="rad/s",
            comment="Gyro",
        ).dict,
    )
    gyro_y: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="rad/s",
            comment="Gyro",
        ).dict,
    )
    gyro_z: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="rad/s",
            comment="Gyro",
        ).dict,
    )


class ModelCommon(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    started: int = pydantic.Field(
        default=0,
        ge=0,
        le=1,
        json_schema_extra=SchemaExtra(
            comment="0: off, 1: started",
        ).dict,
    )

    debuglevel: int = pydantic.Field(
        default=3,
        ge=0,
        le=4,
        json_schema_extra=SchemaExtra(
            comment="0: off, 1: debug, 2: info, 3: warn, 4: error",
        ).dict,
    )


class ModelEMW(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    common: ModelCommon = pydantic.Field(
        default_factory=lambda: ModelCommon(),
    )
    imu_status: ModelImuStatus = pydantic.Field(
        default_factory=lambda: ModelImuStatus(),
    )
