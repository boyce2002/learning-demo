from pydantic import BaseModel, ConfigDict


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AttemptRequest(StrictRequest):
    selected_option: str


class CompleteRequest(StrictRequest):
    reflection: str

