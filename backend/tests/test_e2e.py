import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/health")
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_end_to_end():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        # 1. Список клиентов
        r = await c.get("/clients")
        assert r.status_code == 200
        clients = r.json()
        assert len(clients) >= 1
        client_id = clients[0]["client_id"]

        # 2. Лента
        r = await c.get(f"/clients/{client_id}/feed")
        assert r.status_code == 200
        assert len(r.json()) >= 1

        # 3. Генерация инсайта
        r = await c.post(f"/insights/generate?client_id={client_id}")
        assert r.status_code == 200
        insight = r.json()
        assert insight["what_happened"]
        assert insight["why_it_matters"]
        assert insight["based_on"]
        assert insight["client_features_used"]

        # 4. Трейс
        r = await c.get(f"/insights/{insight['insight_id']}/trace")
        assert r.status_code == 200
        trace = r.json()
        assert len(trace["steps"]) >= 5

        # 5. Follow-up
        r = await c.post(f"/insights/{insight['insight_id']}/ask",
                         json={"question": "Как это повлияет на наши кредиты?"})
        assert r.status_code == 200
        assert r.json()["answer"]

        # 6. Источник
        src_id = insight["based_on"][0]["source_id"]
        r = await c.get(f"/sources/{src_id}")
        assert r.status_code == 200