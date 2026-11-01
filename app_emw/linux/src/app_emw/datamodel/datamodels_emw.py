import typing

import pydantic
from experiment_datadefinitions.utils.util_pydantic import SchemaExtra


class ModelImuSHT40(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    temperature: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="[°C]",
            comment="Temperature",
        ).dict,
    )
    humidity: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="[%]",
            comment="Humidity",
        ).dict,
    )


class ModelM7StatusChannel(pydantic.BaseModel):
    cpp_filename: typing.ClassVar[str] = "m7_status_channel"
    """
    Used to name the generated files, e.g. generated_m7_status_channel_struct.hpp
    """

    model_config = pydantic.ConfigDict(validate_assignment=True)

    tx_ok: int = pydantic.Field(
        default=0,
        json_schema_extra=SchemaExtra(
            unit="[1]",
            comment="Transmit ok count",
        ).dict,
    )

    tx_err: int = pydantic.Field(
        default=0,
        json_schema_extra=SchemaExtra(
            unit="[1]",
            comment="Transmit error count",
        ).dict,
    )

    tx_last_err: int = pydantic.Field(
        default=0,
        json_schema_extra=SchemaExtra(
            unit="[1]",
            comment="Last Transmit Error Code (absolute value)",
        ).dict,
    )
    rx_ok: int = pydantic.Field(
        default=0,
        json_schema_extra=SchemaExtra(
            unit="[1]",
            comment="Receive ok count",
        ).dict,
    )


class ModelM7Status(pydantic.BaseModel):
    cpp_filename: typing.ClassVar[str] = "m7_status"
    """
    Used to name the generated files, e.g. generated_m7_status_struct.hpp
    """

    model_config = pydantic.ConfigDict(validate_assignment=True)

    git_commit: str = pydantic.Field(
        default="",
        json_schema_extra=SchemaExtra(
            comment="The git commit of the firmware source",
            cpp_string_len=64,
        ).dict,
    )
    channel_cmd: ModelM7StatusChannel = pydantic.Field(
        default_factory=lambda: ModelM7StatusChannel(),
    )
    channel_imu: ModelM7StatusChannel = pydantic.Field(
        default_factory=lambda: ModelM7StatusChannel(),
    )


class ModelImuStatus(pydantic.BaseModel):
    cpp_filename: typing.ClassVar[str] = "imu_status"
    """
    Used to name the generated files, e.g. generated_imu_status_struct.hpp
    """

    model_config = pydantic.ConfigDict(validate_assignment=True)

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
            unit="m/s^2",
            comment="Accel",
            format="%0.3f",
        ).dict,
    )
    accel_y: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="m/s^2",
            comment="Accel",
            format="%0.3f",
        ).dict,
    )
    accel_z: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="m/s^2",
            comment="Accel",
            format="%0.3f",
        ).dict,
    )
    gyro_x: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="rad/s",
            comment="Gyro",
            format="%0.3f",
        ).dict,
    )
    gyro_y: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="rad/s",
            comment="Gyro",
            format="%0.3f",
        ).dict,
    )
    gyro_z: float = pydantic.Field(
        default=0.0,
        json_schema_extra=SchemaExtra(
            unit="rad/s",
            comment="Gyro",
            format="%0.3f",
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

    log_imu: int = pydantic.Field(
        default=1,
        ge=0,
        le=1,
        json_schema_extra=SchemaExtra(
            comment="0: off, 1: loggin",
            format="%d",
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


class ModelM7(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    status: ModelM7Status = pydantic.Field(
        default_factory=lambda: ModelM7Status(),
    )
    imu_status: ModelImuStatus = pydantic.Field(
        default_factory=lambda: ModelImuStatus(),
    )


class ModelA53(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    common: ModelCommon = pydantic.Field(
        default_factory=lambda: ModelCommon(),
    )
    sht40_intern: ModelImuSHT40 = pydantic.Field(
        default_factory=lambda: ModelImuSHT40(),
    )
    sht40_extern: ModelImuSHT40 = pydantic.Field(
        default_factory=lambda: ModelImuSHT40(),
    )


class ModelEMW(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    # Same as util_constants.PREFIX_A53
    a53: ModelA53 = pydantic.Field(
        default_factory=lambda: ModelA53(),
    )

    # Same as util_constants.PREFIX_M7
    m7: ModelM7 = pydantic.Field(
        default_factory=lambda: ModelM7(),
    )
