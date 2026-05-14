import pydantic
from pydantic import ConfigDict
print(f"Pydantic version: {pydantic.__version__}")
try:
    conf = {"from_attributes": True}
    print("ConfigDict(from_attributes=True) created successfully")
except Exception as e:
    print(f"Error creating ConfigDict: {e}")
