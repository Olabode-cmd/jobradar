from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...services import companies_service
from ..deps import Conn
from ..schemas.companies import CompanyAddIn, CompanyImportIn
from ..schemas.sources import ToggleIn

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("")
def list_companies(conn: Conn) -> dict[str, Any]:
    return companies_service.list_companies(conn)


@router.post("", status_code=201)
def add_company(body: CompanyAddIn, conn: Conn) -> dict[str, Any]:
    return companies_service.add_company(conn, body.url)


@router.post("/import")
def import_companies(body: CompanyImportIn) -> dict[str, Any]:
    return companies_service.import_companies(body.urls)


@router.post("/seed")
def add_seed_companies() -> dict[str, int]:
    return companies_service.add_seed_companies()


@router.patch("/{provider}/{slug}")
def set_enabled(provider: str, slug: str, body: ToggleIn, conn: Conn) -> dict[str, Any]:
    return companies_service.set_enabled(conn, provider, slug, body.enabled)


@router.delete("/{provider}/{slug}", status_code=204)
def remove_company(provider: str, slug: str) -> None:
    companies_service.remove(provider, slug)
