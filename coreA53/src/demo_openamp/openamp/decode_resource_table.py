#!/usr/bin/env python3
"""
./decode_resource_table.py /lib/firmware/imx8mp_m7_TCM_rpmsg_lite_pingpong_rtos_linux_remote.elf
"""

import argparse
import ctypes
import re
import subprocess
import sys


class ResourceTableHeader(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("version", ctypes.c_uint32),
        ("num_entries", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 2),
    ]


class VirtioDevice(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("resource_type", ctypes.c_uint32),
        ("virtio_id", ctypes.c_uint32),
        ("notify_id", ctypes.c_uint32),
        ("device_features", ctypes.c_uint32),
        ("guest_features", ctypes.c_uint32),
        ("config_length", ctypes.c_uint32),
        ("status", ctypes.c_uint8),
        ("num_vrings", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 2),
    ]


class Vring(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("device_address", ctypes.c_uint32),
        ("alignment", ctypes.c_uint32),
        ("num_descriptors", ctypes.c_uint32),
        ("notify_id", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32),
    ]


class RpmsgResourceTable(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("header", ResourceTableHeader),
        ("offset", ctypes.c_uint32),
        ("vdev", VirtioDevice),
        ("vring0", Vring),
        ("vring1", Vring),
    ]


RESOURCE_TYPES = {3: "RSC_VDEV"}
VIRTIO_IDS = {7: "VIRTIO_ID_RPMSG"}
STATUS_FLAGS = {
    0x01: "ACKNOWLEDGE",
    0x02: "DRIVER",
    0x04: "DRIVER_OK",
    0x08: "FEATURES_OK",
    0x40: "DEVICE_NEEDS_RESET",
    0x80: "FAILED",
}


def read_section(elf_path):
    try:
        result = subprocess.run(
            ["readelf", "-x", ".resource_table", elf_path],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError("readelf was not found in PATH") from None
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or error.stdout.strip()
        raise RuntimeError(message) from None

    section_address = None
    section_data = bytearray()
    line_pattern = re.compile(
        r"^\s*0x([0-9a-fA-F]+)\s+((?:[0-9a-fA-F]{8}(?:\s+|$))+)",
    )

    for line in result.stdout.splitlines():
        match = line_pattern.match(line)
        if not match:
            continue
        if section_address is None:
            section_address = int(match.group(1), 16)
        words = re.findall(r"[0-9a-fA-F]{8}", match.group(2))
        section_data.extend(bytes.fromhex("".join(words)))

    if section_address is None:
        raise RuntimeError("readelf returned no .resource_table data")

    return section_address, bytes(section_data)


def format_status(status):
    names = [name for bit, name in STATUS_FLAGS.items() if status & bit]
    return " | ".join(names) if names else "none"


def print_vring(name, vring, address):
    allocation = "FW_RSC_ADDR_ANY" if vring.device_address == 0xFFFFFFFF else "fixed"
    print(f"{name} @ 0x{address:08x}")
    print(f"  device address : 0x{vring.device_address:08x} ({allocation})")
    print(f"  alignment      : {vring.alignment} (0x{vring.alignment:x})")
    print(f"  descriptors    : {vring.num_descriptors}")
    print(f"  notify ID      : {vring.notify_id}")


def decode(elf_path):
    section_address, data = read_section(elf_path)
    expected_size = ctypes.sizeof(RpmsgResourceTable)
    if len(data) != expected_size:
        raise RuntimeError(
            f"expected an {expected_size}-byte RPMsg resource table, got {len(data)} bytes"
        )

    table = RpmsgResourceTable.from_buffer_copy(data)
    if table.header.num_entries != 1 or table.offset != RpmsgResourceTable.vdev.offset:
        raise RuntimeError(
            "the section is not the supported one-entry RPMsg resource-table layout"
        )

    vdev_address = section_address + RpmsgResourceTable.vdev.offset
    status_address = vdev_address + VirtioDevice.status.offset
    print(f"ELF: {elf_path}")
    print(f"resource table @ 0x{section_address:08x}, size {len(data)} bytes")
    print(f"  version        : {table.header.version}")
    print(f"  entries        : {table.header.num_entries}")
    print(f"  entry[0] offset: 0x{table.offset:08x}")
    print(f"virtio device @ 0x{vdev_address:08x}")
    print(
        f"  resource type  : {table.vdev.resource_type} "
        f"({RESOURCE_TYPES.get(table.vdev.resource_type, 'unknown')})"
    )
    print(
        f"  virtio ID      : {table.vdev.virtio_id} "
        f"({VIRTIO_IDS.get(table.vdev.virtio_id, 'unknown')})"
    )
    print(f"  notify ID      : {table.vdev.notify_id}")
    print(f"  device features: 0x{table.vdev.device_features:08x}")
    print(f"  guest features : 0x{table.vdev.guest_features:08x}")
    print(
        f"  status         : 0x{table.vdev.status:02x} "
        f"({format_status(table.vdev.status)}) @ 0x{status_address:08x}"
    )
    print(f"  vrings         : {table.vdev.num_vrings}")
    print_vring(
        "vring0",
        table.vring0,
        section_address + RpmsgResourceTable.vring0.offset,
    )
    print_vring(
        "vring1",
        table.vring1,
        section_address + RpmsgResourceTable.vring1.offset,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Decode an ELF .resource_table section using readelf and ctypes."
    )
    parser.add_argument("elf", help="ELF firmware image")
    args = parser.parse_args()

    try:
        decode(args.elf)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
