from pydantic import BaseModel, Field


class ClientProductFlags(BaseModel):
    rko: bool = False
    garantii: bool = False
    credit: bool = False
    leasing: bool = False
    deposit: bool = False
    salary_project: bool = False
    factoring: bool = False


class ClientProfile(BaseModel):
    client_id: str
    name: str
    industry: str                       # MAINOKVED_NAME
    okved_code: str
    revenue_billion_rub: float
    region: str
    city: str
    company_age_years: int
    workers: str
    client_type: str                    # "active" | "potential"
    products: ClientProductFlags
    counterparties: list[str] = Field(default_factory=list)
    ftn_countries: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)     # для быстрой фильтрации