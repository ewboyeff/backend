from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends

from app.core.security import require_role
from app.models.user import UserRole

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_RESEARCH_FILE = _DATA_DIR / "research_stats.json"

DEFAULT_STATS: dict = {
    "report": {
        "statActive": "120+",
        "statBeneficiaries": "850K+",
        "statRaised": "₿ 45B",
        "statTransparency": "68%",
        "areaPcts": [38, 28, 19, 15],
        "findingsValues": ["87 ta", "6 ta", "21 ta", "62.4", "+8.3%"],
    },
    "analysis": {
        "statNewFunds": "+23%",
        "statOnlineReports": "+41%",
        "statUserRatings": "+18%",
        "growingChanges": ["+34%", "+29%", "+22%", "+17%"],
        "avgValues": ["51.2 ball", "57.6 ball (+6.4)", "62.4 ball (+4.8)"],
    },
    "comparison": {
        "countryScores": [74, 61, 62, 48, 31],
        "globalValues": ["58.3 ball", "79.1 ball", "55.2 ball", "2-o'rin"],
    },
}

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/research")
async def get_research_stats() -> dict:
    if _RESEARCH_FILE.exists():
        return json.loads(_RESEARCH_FILE.read_text(encoding="utf-8"))
    return DEFAULT_STATS


@router.put(
    "/research",
    dependencies=[Depends(require_role(UserRole.admin))],
)
async def update_research_stats(data: dict) -> dict:
    _DATA_DIR.mkdir(exist_ok=True)
    _RESEARCH_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return data
