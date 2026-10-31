import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_DATA = DIRECTORY_OF_THIS_FILE.parent.parent.parent.parent / "data"
assert DIRECTORY_DATA.is_dir()


PREFIX_M7 = "/m7"
PREFIX_M53 = "/a53"


# These must match the endpoint names in main.cpp.
CHANNEL_NAME_CMD: str = "rpmsg-emw-CMD"
CHANNEL_NAME_IMU: str = "rpmsg-emw-IMU"
