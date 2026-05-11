"""
Automatic index score calculation.

Called as a background task whenever fund data changes:
- fund created / updated
- project created / updated
- financial report created / updated

For each active IndexFactor, we match its name_uz against a keyword map
and call the corresponding scoring function.  Factors whose names contain
"skip" keywords (audit, hamkor, media …) are left untouched so admins can
score them manually.

After computing partial scores we call IndexService.calculate(), which
merges them with any existing manual scores and writes the weighted result.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.fund import Fund
from app.models.index import IndexFactor
from app.models.project import Project, ProjectStatus
from app.models.report import FinancialReport, ReportType
from app.repositories.index import IndexRepository
from app.schemas.index import FactorScoreInput, IndexCalculateRequest
from app.services.index import IndexService

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Factor scoring functions
# signature: (fund, reports, projects) -> (score: Decimal, note: str)
# ---------------------------------------------------------------------------

ScoringFn = Callable[
    [Fund, list[FinancialReport], list[Project]],
    tuple[Decimal, str],
]


def _score_website(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    if fund.website_url:
        return Decimal("100"), "Veb-sayt mavjud"
    return Decimal("0"), "Veb-sayt ko'rsatilmagan"


def _score_telegram(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    if fund.telegram_url:
        return Decimal("100"), "Telegram kanali mavjud"
    return Decimal("0"), "Telegram kanali yo'q"


def _score_instagram(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    if fund.instagram_url:
        return Decimal("85"), "Instagram sahifasi mavjud"
    return Decimal("0"), "Instagram sahifasi yo'q"


def _score_social(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    score = 0
    parts: list[str] = []
    if fund.telegram_url:
        score += 60
        parts.append("Telegram")
    if fund.instagram_url:
        score += 40
        parts.append("Instagram")
    note = ", ".join(parts) if parts else "Ijtimoiy tarmoqlar yo'q"
    return Decimal(str(score)), note


def _score_annual_report(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    count = sum(1 for r in reports if r.report_type == ReportType.annual)
    if count >= 3:
        return Decimal("100"), f"{count} ta yillik hisobot"
    elif count == 2:
        return Decimal("80"), f"{count} ta yillik hisobot"
    elif count == 1:
        return Decimal("60"), "1 ta yillik hisobot"
    return Decimal("0"), "Yillik hisobot yo'q"


def _score_quarterly_report(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    count = sum(1 for r in reports if r.report_type == ReportType.quarterly)
    if count >= 8:
        return Decimal("100"), f"{count} ta choraklik hisobot"
    elif count >= 4:
        return Decimal("80"), f"{count} ta choraklik hisobot"
    elif count >= 2:
        return Decimal("60"), f"{count} ta choraklik hisobot"
    elif count == 1:
        return Decimal("40"), "1 ta choraklik hisobot"
    return Decimal("0"), "Choraklik hisobotlar yo'q"


def _score_monthly_report(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    count = sum(1 for r in reports if r.report_type == ReportType.monthly)
    if count >= 12:
        return Decimal("100"), f"{count} ta oylik hisobot"
    elif count >= 6:
        return Decimal("75"), f"{count} ta oylik hisobot"
    elif count >= 1:
        return Decimal(str(min(count * 8, 60))), f"{count} ta oylik hisobot"
    return Decimal("0"), "Oylik hisobotlar yo'q"


def _score_financial_report(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    has_income = any(r.total_income > 0 for r in reports)
    has_expense = any(r.total_expense > 0 for r in reports)
    if has_income and has_expense:
        return Decimal("90"), "Kirim va chiqim hisobotlari mavjud"
    elif has_income or has_expense:
        return Decimal("60"), "Qisman moliyaviy hisobot mavjud"
    elif reports:
        return Decimal("30"), f"{len(reports)} ta hisobot mavjud (moliyaviy ma'lumotlarsiz)"
    return Decimal("0"), "Moliyaviy hisobotlar yo'q"


def _score_general_reports(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    count = len(reports)
    if count == 0:
        return Decimal("0"), "Hisobotlar yo'q"
    score = min(count * 15, 90)
    return Decimal(str(score)), f"{count} ta hisobot mavjud"


def _score_projects(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    total = len(projects)
    if total == 0:
        return Decimal("0"), "Loyihalar yo'q"
    completed = sum(1 for p in projects if p.status == ProjectStatus.completed)
    active = sum(1 for p in projects if p.status == ProjectStatus.active)
    count_score = min(total * 8, 50)
    ratio = completed / total if total > 0 else 0
    ratio_score = int(ratio * 50)
    score = min(count_score + ratio_score, 100)
    return Decimal(str(score)), f"{total} ta loyiha ({completed} ta yakunlangan, {active} ta faol)"


def _score_beneficiaries(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    total = sum(p.beneficiaries_count for p in projects)
    if total == 0:
        return Decimal("0"), "Benefitsidarlar ko'rsatilmagan"
    if total >= 10000:
        score = 100
    elif total >= 5000:
        score = 90
    elif total >= 1000:
        score = 80
    elif total >= 500:
        score = 70
    elif total >= 100:
        score = 55
    elif total >= 10:
        score = 40
    else:
        score = 25
    return Decimal(str(score)), f"{total} nafar benefitsidar"


def _score_inn(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    if fund.inn:
        return Decimal("90"), f"INN: {fund.inn}"
    return Decimal("0"), "INN ko'rsatilmagan"


def _score_legal(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    if fund.inn and fund.registration_number:
        return Decimal("90"), "INN va ro'yxatdan o'tish raqami mavjud"
    elif fund.inn:
        return Decimal("70"), "INN mavjud"
    elif fund.registration_number:
        return Decimal("50"), "Ro'yxatdan o'tish raqami mavjud"
    return Decimal("20"), "Huquqiy hujjatlar to'liq emas"


def _score_registration(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    if fund.inn or fund.registration_number:
        reg = fund.registration_number or ""
        return Decimal("90"), f"Ro'yxatdan o'tgan: {reg}"
    return Decimal("0"), "Ro'yxatdan o'tmagan"


def _score_donation(
    fund: Fund,
    reports: list[FinancialReport],
    projects: list[Project],
) -> tuple[Decimal, str]:
    if fund.donation_url:
        return Decimal("100"), "Xayriya havolasi mavjud"
    return Decimal("0"), "Xayriya havolasi yo'q"


# ---------------------------------------------------------------------------
# Ordered keyword → scoring function map
# More specific patterns come first so they take priority.
# ---------------------------------------------------------------------------

FACTOR_SCORING_MAP: list[tuple[str, ScoringFn]] = [
    # Most specific first
    ("yillik",          _score_annual_report),
    ("choraklik",       _score_quarterly_report),
    ("oylik",           _score_monthly_report),
    ("moliyaviy",       _score_financial_report),
    ("kirim",           _score_financial_report),
    ("chiqim",          _score_financial_report),
    ("telegram",        _score_telegram),
    ("instagram",       _score_instagram),
    ("ijtimoiy",        _score_social),
    ("veb-sayt",        _score_website),
    ("veb sayt",        _score_website),
    ("vebsayt",         _score_website),
    ("website",         _score_website),
    ("sayt",            _score_website),
    ("xayriya havolasi", _score_donation),
    ("xayriya",         _score_donation),
    ("loyiha",          _score_projects),
    ("benefitsiar",     _score_beneficiaries),
    ("foydalanuvchi",   _score_beneficiaries),
    ("inn",             _score_inn),
    ("huquqiy",         _score_legal),
    ("ro'yxat",         _score_registration),
    ("royxat",          _score_registration),
    ("qayd",            _score_registration),
    ("hisobot",         _score_general_reports),   # catch-all for reports
]

# Factor names containing these keywords are skipped (manual scoring only)
SKIP_KEYWORDS: tuple[str, ...] = (
    "audit",
    "hamkor",
    "media",
    "ommaviy",
    "intervyu",
    "press",
    "maqola",
    "nashr",
)


def _find_scoring_fn(factor: IndexFactor) -> ScoringFn | None:
    name = factor.name_uz.lower()
    for keyword, fn in FACTOR_SCORING_MAP:
        if keyword in name:
            return fn
    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def auto_calculate_fund_index(fund_id: UUID) -> None:
    """
    Background task: open a fresh DB session, score all auto-scorable
    factors for the given fund, and call IndexService.calculate().
    """
    async with AsyncSessionLocal() as db:
        try:
            # Load fund with projects and reports
            result = await db.execute(
                select(Fund)
                .options(
                    selectinload(Fund.projects),
                    selectinload(Fund.reports),
                )
                .where(Fund.id == fund_id)
            )
            fund = result.scalar_one_or_none()
            if fund is None:
                log.warning("auto_calculate_fund_index: fund %s not found", fund_id)
                return

            projects: list[Project] = list(fund.projects)
            reports: list[FinancialReport] = list(fund.reports)

            # Load all active factors
            idx_repo = IndexRepository(db)
            factors: list[IndexFactor] = await idx_repo.get_active_factors()

            if not factors:
                log.info("auto_calculate_fund_index: no active factors, skipping")
                return

            # Build auto-scored factor inputs
            scores: list[FactorScoreInput] = []
            skipped: list[str] = []

            for factor in factors:
                name_lower = factor.name_uz.lower()

                # Skip factors reserved for manual scoring
                if any(kw in name_lower for kw in SKIP_KEYWORDS):
                    skipped.append(factor.name_uz)
                    continue

                scoring_fn = _find_scoring_fn(factor)
                if scoring_fn is None:
                    log.debug(
                        "auto_calculate_fund_index: no scoring fn for factor '%s', skipping",
                        factor.name_uz,
                    )
                    continue

                score, note = scoring_fn(fund, reports, projects)
                scores.append(
                    FactorScoreInput(
                        factor_id=factor.id,
                        score=score,
                        note=note,
                    )
                )

            if not scores:
                log.info(
                    "auto_calculate_fund_index: no auto-scored factors for fund %s",
                    fund_id,
                )
                return

            log.info(
                "auto_calculate_fund_index: fund %s — scoring %d factors, skipping %d manual factors",
                fund_id,
                len(scores),
                len(skipped),
            )

            # Delegate to IndexService (handles upsert + weighted calculation)
            service = IndexService(db)
            await service.calculate(
                fund_id=fund_id,
                data=IndexCalculateRequest(scores=scores),
            )
            await db.commit()

            log.info("auto_calculate_fund_index: fund %s index updated successfully", fund_id)

        except Exception as exc:
            await db.rollback()
            log.exception(
                "auto_calculate_fund_index: failed for fund %s: %s", fund_id, exc
            )
