from __future__ import annotations

import pathlib

from demo_openamp.datamodel.model import unittests_nested
from demo_openamp.datamodel.utils import util_pydantic

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


def test_datamodel_nested_duallist() -> None:
    model_duallist = unittests_nested.ModelSystemDualList()
    (DIRECTORY_OF_THIS_FILE / "model_duallist.py").write_text(
        repr(model_duallist.model_json_schema())
    )

    print("*******")
    mh = util_pydantic.ModelHierarchy.factory(model=model_duallist)
    elements = mh.all_elements
    assert len(elements) == 13
    path_vs_value = [(e.path, e.value) for e in elements]
    assert path_vs_value == [
        ("/debuglevel", 4095),
        ("/axis_x/name", "Axis X"),
        ("/axis_x/value", 4095),
        ("/axis_x/i_param", 0.25),
        ("/axis_y/name", "Axis Y"),
        ("/axis_y/value", 4095),
        ("/axis_y/i_param", 0.25),
        ("/controllers/0/name", "Axis R"),
        ("/controllers/0/value", 4095),
        ("/controllers/0/i_param", 0.25),
        ("/controllers/1/name", "Axis S"),
        ("/controllers/1/value", 4095),
        ("/controllers/1/i_param", 0.25),
    ]
    x = mh.get_by_path("/controllers/1/name")
    assert x.value == "Axis S"
    print("+++")
    pass


def test_datamodel_nested_list() -> None:
    model_list = unittests_nested.ModelSystemList()
    assert len(model_list.controllers) == 2
    (DIRECTORY_OF_THIS_FILE / "schema_model_list.py").write_text(
        repr(model_list.model_json_schema())
    )

    print("*******")
    mh = util_pydantic.ModelHierarchy.factory(model=model_list)
    mh.dump()
    print("+++")
    pass


def main() -> None:
    test_datamodel_nested_duallist()
    test_datamodel_nested_list()


if __name__ == "__main__":
    main()
