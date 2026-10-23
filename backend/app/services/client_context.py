from app.schemas.client import ClientProfile, ClientProductFlags
from app.storage import store


_MOCK_CLIENTS = [
    ClientProfile(
        client_id="CL-001",
        name="СтройМонолитГрупп",
        industry="Строительство жилых и нежилых зданий",
        okved_code="41.20",
        revenue_billion_rub=22.5,
        region="Москва",
        city="Москва",
        company_age_years=14,
        workers="1000-5000",
        client_type="active",
        products=ClientProductFlags(
            rko=True, credit=True, garantii=True, leasing=True, factoring=False,
            deposit=False, salary_project=True,
        ),
        counterparties=["CL-002", "CL-003"],
        ftn_countries=["Китай", "Турция"],
        tags=["construction", "borrower"],
    ),
    ClientProfile(
        client_id="CL-002",
        name="ЗолотоТрейд",
        industry="Добыча золота",
        okved_code="07.29",
        revenue_billion_rub=31.0,
        region="Магаданская область",
        city="Магадан",
        company_age_years=22,
        workers="500-1000",
        client_type="active",
        products=ClientProductFlags(rko=True, credit=False, factoring=True, deposit=True),
        counterparties=["CL-001"],
        ftn_countries=["ОАЭ", "Китай"],
        tags=["mining", "gold", "exporter"],
    ),
    ClientProfile(
        client_id="CL-003",
        name="РегионРитейл",
        industry="Розничная торговля продуктами",
        okved_code="47.11",
        revenue_billion_rub=18.2,
        region="Санкт-Петербург",
        city="Санкт-Петербург",
        company_age_years=9,
        workers="5000+",
        client_type="active",
        products=ClientProductFlags(rko=True, deposit=True, salary_project=True),
        counterparties=["CL-001"],
        ftn_countries=[],
        tags=["retail", "consumer"],
    ),
]


async def get_profile(client_id: str) -> ClientProfile | None:
    for c in _MOCK_CLIENTS:
        if c.client_id == client_id:
            if c.client_id not in store.clients:
                store.clients[c.client_id] = c
            return c
    return None


async def list_profiles() -> list[ClientProfile]:
    for c in _MOCK_CLIENTS:
        store.clients[c.client_id] = c
    return list(_MOCK_CLIENTS)