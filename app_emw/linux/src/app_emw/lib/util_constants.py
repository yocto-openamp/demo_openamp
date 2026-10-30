import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_DATA = DIRECTORY_OF_THIS_FILE.parent.parent.parent.parent / "data"
assert DIRECTORY_DATA.is_dir()

IMU_MEASUREMENTS_FILE = DIRECTORY_DATA / "imu_measurements.bin"
