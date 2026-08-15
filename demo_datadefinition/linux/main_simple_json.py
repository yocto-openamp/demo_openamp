from pydantic import BaseModel


class DataModel(BaseModel):
    name: str
    value: int


if __name__ == "__main__":
    sample = DataModel(name="example", value=1)
    print(sample.model_dump_json())
