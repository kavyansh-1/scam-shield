import json
import re
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select

from ..models.db import BlocklistEntry, SessionLocal
from ..models.schemas import BlocklistHit, Entities


def normalize_value(value: str, kind: str) -> str:
    v = value.strip().lower()
    if kind == "phone":
        return re.sub(r"\D", "", v)[-10:]
    if kind == "url":
        host = urlparse(v if "://" in v else "//" + v).netloc or v
        return host.split("/")[0].removeprefix("www.")
    return v


async def seed_blocklist() -> None:
    data = json.loads((Path(__file__).parent.parent / "data" / "blocklist_seed.json").read_text(encoding="utf-8"))
    async with SessionLocal() as s:
        for d in data:
            if not await s.get(BlocklistEntry, (d["value"], d["kind"])):
                s.add(BlocklistEntry(value=d["value"], kind=d["kind"], reports=d["reports"]))
        await s.commit()


async def check_entities(ent: Entities) -> list[BlocklistHit]:
    pairs = [(v, "phone") for v in ent.phones] + [(v, "upi") for v in ent.upi_ids] + [(v, "url") for v in ent.urls]
    hits: list[BlocklistHit] = []
    if not pairs:
        return hits
    async with SessionLocal() as s:
        for raw, kind in pairs:
            row = (await s.execute(select(BlocklistEntry).where(
                BlocklistEntry.value == normalize_value(raw, kind), BlocklistEntry.kind == kind))).scalar_one_or_none()
            if row:
                hits.append(BlocklistHit(value=raw, kind=kind, reports=row.reports))
    return hits


async def report_value(value: str, kind: str) -> int:
    nv = normalize_value(value, kind)
    async with SessionLocal() as s:
        row = await s.get(BlocklistEntry, (nv, kind))
        if row:
            row.reports += 1
        else:
            row = BlocklistEntry(value=nv, kind=kind, reports=1)
            s.add(row)
        await s.commit()
        return row.reports
