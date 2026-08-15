import pathlib
import re
import shutil
import subprocess

import pytest
from demo_openamp.datamodel.model import unittests_simple
from demo_openamp.datamodel.renderer import renderer_c

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_SRC_C = DIRECTORY_OF_THIS_FILE / "src_c"


def test_src_c() -> None:
    gcc = shutil.which("gcc")
    if gcc is None:
        pytest.skip("gcc not installed")

    model = unittests_simple.ModelPidController(name="Axis W", value=42, i_param=3.14)
    renderer = renderer_c.RendererC(model=model)

    def generate_compile() -> None:
        """
        TODO: Clearer interface
        """

        def generate(filename: pathlib.Path, source: str) -> None:
            filename.write_text(source)

        generate(
            DIRECTORY_SRC_C / "generated_pid_controller_struct.h",
            renderer.render_c_struct(),
        )
        generate(
            DIRECTORY_SRC_C / "generated_pid_controller_initializer.h",
            renderer.render_c_initializer(),
        )

        subprocess.run(
            [gcc, "-Wall", "-Wextra", "dump_values.c", "-o", "dump_values"],
            cwd=DIRECTORY_SRC_C,
            check=True,
        )

    def run() -> bytes:
        """
        TODO: Clearer interface
        """
        result = subprocess.run(
            ["./dump_values"],
            cwd=DIRECTORY_SRC_C,
            check=True,
            capture_output=True,
            text=True,
        )

        stdout = result.stdout.strip()
        match = re.fullmatch(r">0x(?P<hexstring>[0-9A-F]+)<", stdout)
        assert match is not None
        hexstring = match.group("hexstring")
        serialized = bytes.fromhex(hexstring)
        return serialized

    generate_compile()
    serialized = run()

    model3 = renderer.deserialize_from_c(serizalized=serialized)
    assert isinstance(model3, unittests_simple.ModelPidController)
    assert model3.name == model.name
    assert model3.value == model.value
    assert model3.i_param == model.i_param
