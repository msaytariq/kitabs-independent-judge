"""HTTP envelope validation; domain command rules live outside the API."""
from pydantic import BaseModel,ConfigDict,Field,StrictInt


class CreateEditorialReview(BaseModel):
    model_config=ConfigDict(extra='forbid')
    scope_id:str=Field(min_length=1,max_length=64)
    rubric:str=Field(min_length=1,max_length=8000)
    actor:str=Field(min_length=1,max_length=80)


class EditorialCommand(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_revision:StrictInt=Field(ge=0)
    command_id:str=Field(pattern=r'^[A-Za-z0-9_-]{1,80}$')
    actor:str=Field(min_length=1,max_length=80)
    kind:str=Field(min_length=1,max_length=40)
    params:dict
