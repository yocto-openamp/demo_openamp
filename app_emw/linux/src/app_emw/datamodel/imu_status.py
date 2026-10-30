import pydantic

from utils.util_pydantic import SchemaExtra

PREFIX_M7 = "/m7"

"""
typedef struct __attribute__((packed)) {
    msg_header header;
    uint64_t timestamp; // us since boot
    int32_t measurement_count;
    int32_t measurement_count_error;
    float accel_x; // accel: um/s^2, gyro: urad/s
    float accel_y;
    float accel_z;
    uint8_t accel; // 1: accel, 0: gyro
} msg_imu_status;
"""


class ModelImuStatus(pydantic.BaseModel):
    timestamp: int = pydantic.Field(
        default=0,
        json_schema_extra=SchemaExtra(
            unit="us",
            comment="Timestamp",
        ).dict,
    )
    measurement_count: int = pydantic.Field(
        default=4095,
        ge=-4095,
        le=4095,
        json_schema_extra=SchemaExtra(
            unit="[1]",
            comment="Count of measurements attempts",
        ).dict,
    )
    measurement_count_error: int = pydantic.Field(
        default=4095,
        ge=-4095,
        le=4095,
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
    is_accel: int = pydantic.Field(
        default=1,
        json_schema_extra=SchemaExtra(
            unit="[0, 1]",
            comment="1: accel, 0: gyro",
        ).dict,
    )
