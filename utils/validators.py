# utils/validators.py
from pydantic import BaseModel, field_validator

class QueryInput(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty.")
        if len(v) < 5:
            raise ValueError("Query too short — please be more specific.")
        if len(v) > 500:
            raise ValueError(f"Query too long ({len(v)} chars) — max 500.")
        banned = ["<script>", "DROP TABLE", "rm -rf"]
        for b in banned:
            if b.lower() in v.lower():
                raise ValueError("Query contains invalid content.")
        return v