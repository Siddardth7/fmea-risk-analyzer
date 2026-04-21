"""
schema.py
Pydantic v2 domain models for FMEA data validation.
Single source of truth for field types, constraints, and dataset-level rules.
"""
from __future__ import annotations
from typing import Annotated
import pydantic


class FMEARow(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(strict=True)

    ID: int = pydantic.Field(gt=0)
    Process_Step: str = pydantic.Field(min_length=1)
    Component: str = pydantic.Field(min_length=1)
    Function: str = pydantic.Field(min_length=1)
    Failure_Mode: str = pydantic.Field(min_length=1)
    Effect: str = pydantic.Field(min_length=1)
    Severity: Annotated[int, pydantic.Field(ge=1, le=10)]
    Cause: str = pydantic.Field(min_length=1)
    Occurrence: Annotated[int, pydantic.Field(ge=1, le=10)]
    Current_Control: str = pydantic.Field(min_length=1)
    Detection: Annotated[int, pydantic.Field(ge=1, le=10)]

    @property
    def RPN(self) -> int:
        return self.Severity * self.Occurrence * self.Detection


class FMEADataset(pydantic.BaseModel):
    rows: list[FMEARow]

    @pydantic.model_validator(mode="after")
    def check_no_duplicate_ids(self) -> "FMEADataset":
        ids = [row.ID for row in self.rows]
        seen: set[int] = set()
        dupes = [i for i in ids if i in seen or seen.add(i)]  # type: ignore[func-returns-value]
        if dupes:
            raise ValueError(f"duplicate IDs found: {dupes}")
        return self
