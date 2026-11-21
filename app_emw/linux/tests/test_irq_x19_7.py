import ctypes
import typing

from app_emw.datamodel import datamodels_emw
from app_emw.lib import util_cmd_to_a53
from app_emw.lib.util_cmd import MsgHeader
from experiment_datadefinitions.renderer.renderer_cpp import RendererCPP


def test_irq_x19_7_cpp_layout() -> None:
    """The packed layout must match the generated fixed-width signal fields."""
    renderer = RendererCPP(model=datamodels_emw.ModelIrqX19_7())
    assert ctypes.sizeof(renderer.ctypes_model) == 8 + 2 + 2 + 2


def test_irq_x19_7_struct_contains_dropped_counter() -> None:
    renderer = RendererCPP(model=datamodels_emw.ModelIrqX19_7())
    assert "uint16_t irq_dropped_counter;" in renderer.render_cpp_struct()


def test_irq_x19_7_is_dispatched_and_deserialized() -> None:
    class Handler(util_cmd_to_a53.HandlerCmdA53):
        irq_signal: datamodels_emw.ModelIrqX19_7 | None = None

        @typing.override
        def handle_imu_status(
            self, imu_status: datamodels_emw.ModelImuStatus
        ) -> None:
            raise AssertionError("unexpected")

        @typing.override
        def handle_m7_status(self, m7_status: datamodels_emw.ModelM7Status) -> None:
            raise AssertionError("unexpected")

        @typing.override
        def handle_irq_x19_7(self, irq_signal: datamodels_emw.ModelIrqX19_7) -> None:
            self.irq_signal = irq_signal

    renderer = RendererCPP(model=datamodels_emw.ModelIrqX19_7())
    payload = renderer.serialize_to_cpp(
        datamodels_emw.ModelIrqX19_7(
            irq_timestamp_us=123_456_789_012,
            irq_counter=42,
            irq_dropped_counter=13,
            is_interrupt=True,
        )
    )
    header = MsgHeader(
        msg_id=util_cmd_to_a53.MSG_ID_M7_to_A53.IRQ_X19_7,
        msg_size=ctypes.sizeof(MsgHeader) + len(payload),
    )

    handler = Handler()
    handler._handle_msg(header=header, payload_rpmsg=bytes(header) + payload)

    assert handler.irq_signal == datamodels_emw.ModelIrqX19_7(
        irq_timestamp_us=123_456_789_012,
        irq_counter=42,
        irq_dropped_counter=13,
        is_interrupt=True,
    )
