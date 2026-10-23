from fastapi import APIRouter, HTTPException
from app.services import client_context
from app.schemas.client import ClientProfile

router = APIRouter()


@router.get("", response_model=list[ClientProfile])
async def list_clients():
    return await client_context.list_profiles()


@router.get("/{client_id}", response_model=ClientProfile)
async def get_client(client_id: str):
    c = await client_context.get_profile(client_id)
    if not c:
        raise HTTPException(404, "Client not found")
    return c