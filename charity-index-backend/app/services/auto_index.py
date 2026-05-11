"""
Automatic index score calculation.

Called as a background task whenever fund data changes:
- fund created / updated
- project created / updated
- financial report created / updated

For each active IndexFactor we match its name_uz (lowercased) against an
ordered keyword map and call the corresponding scoring function.
Factors whose names contain SKIP_KEYWORDS are left untouched so admins
can score them manually.
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

ScoringFn = Callable[
    [Fund, list[FinancialReport], list[Project]],
    tuple[Decimal, str],
]

# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def _score_website(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    if fund.website_url:
        return Decimal("100"), "Rasmiy veb-sayt mavjud"
    return Decimal("0"), "Veb-sayt ko'rsatilmagan"


def _score_telegram(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    if fund.telegram_url:
        return Decimal("100"), "Telegram kanali mavjud"
    return Decimal("0"), "Telegram kanali yo'q"


def _score_instagram(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    if fund.instagram_url:
        return Decimal("85"), "Instagram sahifasi mavjud"
    return Decimal("0"), "Instagram sahifasi yo'q"


def _score_social(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Ijtimoiy tarmoqlarda faollik — Telegram + Instagram."""
    score = 0
    parts: list[str] = []
    if fund.telegram_url:
        score += 60
        parts.append("Telegram")
    if fund.instagram_url:
        score += 40
        parts.append("Instagram")
    note = (", ".join(parts) + " faol") if parts else "Ijtimoiy tarmoqlar yo'q"
    return Decimal(str(score)), note


def _score_media(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Media e'tiboroti va obro' — website + Telegram + Instagram mavjudligi."""
    score = 0
    parts: list[str] = []
    if fund.website_url:
        score += 40
        parts.append("Veb-sayt")
    if fund.telegram_url:
        score += 35
        parts.append("Telegram")
    if fund.instagram_url:
        score += 25
        parts.append("Instagram")
    if not parts:
        return Decimal("0"), "Ijtimoiy tarmoqlar va veb-sayt yo'q"
    return Decimal(str(min(score, 100))), ", ".join(parts) + " orqali onlayn faollik"


def _score_financial_report(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Moliyaviy hisobot e'lon qilish."""
    annual = sum(1 for r in reports if r.report_type == ReportType.annual)
    quarterly = sum(1 for r in reports if r.report_type == ReportType.quarterly)
    monthly = sum(1 for r in reports if r.report_type == ReportType.monthly)
    total = len(reports)
    if total == 0:
        return Decimal("0"), "Moliyaviy hisobotlar yo'q"
    if annual >= 2:
        score = 95
    elif annual == 1:
        score = 85
    elif quarterly >= 4:
        score = 80
    elif quarterly >= 2:
        score = 65
    elif quarterly >= 1 or monthly >= 6:
        score = 50
    else:
        score = 30
    return Decimal(str(score)), f"Hisobotlar: {annual} yillik, {quarterly} choraklik, {monthly} oylik"


def _score_project_reports(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Loyihalar bo'yicha hisobot — loyihalar VA hisobotlar birgalikda."""
    has_p = len(projects) > 0
    has_r = len(reports) > 0
    if has_p and has_r:
        return Decimal("90"), f"{len(projects)} ta loyiha, {len(reports)} ta hisobot"
    elif has_r:
        return Decimal("55"), f"{len(reports)} ta hisobot mavjud (loyihasiz)"
    elif has_p:
        return Decimal("35"), f"{len(projects)} ta loyiha mavjud (hisobotsiz)"
    return Decimal("0"), "Loyihalar va hisobotlar yo'q"


def _score_expenses(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Xarajatlar tarkibini oshkor etish — hisobot va loyihalardan xarajatlar."""
    report_expense = sum(r.total_expense for r in reports if r.total_expense)
    project_spent = sum(p.spent for p in projects if p.spent)
    total = report_expense + project_spent

    if total <= 0:
        return Decimal("0"), "Xarajatlar ko'rsatilmagan"
    if report_expense > 0 and project_spent > 0:
        score = 95
        note = f"Hisobot xarajati + loyiha xarajati mavjud"
    elif report_expense > 0:
        score = 85
        note = f"Moliyaviy hisobotda xarajatlar ko'rsatilgan"
    else:
        score = 65
        note = f"Loyihalarda xarajatlar ko'rsatilgan"
    return Decimal(str(score)), note


def _score_donor_income(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Donor mablag'larini hisoblash — kirim va byudjet ma'lumotlari."""
    report_income = sum(r.total_income for r in reports if r.total_income)
    project_budget = sum(p.budget for p in projects if p.budget)
    total = report_income + project_budget

    if total <= 0:
        return Decimal("0"), "Donor mablag'lari ko'rsatilmagan"
    if report_income > 0 and project_budget > 0:
        score = 95
        note = "Hisobot kirim + loyiha byudjeti mavjud"
    elif report_income > 0:
        score = 85
        note = "Moliyaviy hisobotda kirim ko'rsatilgan"
    else:
        score = 65
        note = "Loyihalarda byudjet ko'rsatilgan"
    return Decimal(str(score)), note


def _score_project_completion(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Loyihalar muvaffaqiyatli yakunlanishi."""
    if not projects:
        return Decimal("0"), "Loyihalar yo'q"
    total = len(projects)
    completed = sum(1 for p in projects if p.status == ProjectStatus.completed)
    active = sum(1 for p in projects if p.status == ProjectStatus.active)
    ratio = completed / total

    if ratio >= 0.8:
        score = 100
    elif ratio >= 0.6:
        score = 85
    elif ratio >= 0.4:
        score = 70
    elif ratio >= 0.2:
        score = 50
    elif completed > 0:
        score = 30
    else:
        # Has projects but none completed — still gets small credit for active ones
        score = max(10, min(active * 5, 20))
    return Decimal(str(score)), f"{completed}/{total} ta loyiha yakunlangan ({int(ratio * 100)}%)"


def _score_beneficiary_list(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Benefitsiarlar ro'yxati — loyihalarda benefitsidarlar ko'rsatilganmi."""
    projects_with_ben = [p for p in projects if p.beneficiaries_count > 0]
    if projects_with_ben:
        total = sum(p.beneficiaries_count for p in projects_with_ben)
        return Decimal("85"), f"{total} nafar benefitsidar ro'yxati mavjud"
    elif projects:
        return Decimal("20"), f"{len(projects)} ta loyiha bor, benefitsidarlar ko'rsatilmagan"
    return Decimal("0"), "Loyihalar va benefitsidarlar yo'q"


def _score_beneficiary_count(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Benefitsiarlar soni — umumiy nafar soni."""
    total = sum(p.beneficiaries_count for p in projects)
    if total == 0:
        return Decimal("0"), "Benefitsidarlar soni ko'rsatilmagan"
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
    return Decimal(str(score)), f"Jami {total} nafar benefitsidar"


def _score_inn(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    if fund.inn:
        return Decimal("90"), f"INN: {fund.inn}"
    return Decimal("0"), "INN ko'rsatilmagan"


def _score_legal(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Huquqiy hujjatlar mavjudligi."""
    if fund.inn and fund.registration_number:
        return Decimal("90"), f"INN va ro'yxatdan o'tish raqami mavjud"
    elif fund.inn:
        return Decimal("70"), f"INN mavjud: {fund.inn}"
    elif fund.registration_number:
        return Decimal("50"), f"Ro'yxatdan o'tish raqami mavjud"
    return Decimal("20"), "Huquqiy hujjatlar to'liq emas"


def _score_registration(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    """Davlat ro'yxatidan o'tganlik."""
    if fund.inn and fund.registration_number:
        return Decimal("95"), f"INN: {fund.inn}, raqam: {fund.registration_number}"
    elif fund.inn:
        return Decimal("85"), f"INN: {fund.inn}"
    elif fund.registration_number:
        return Decimal("70"), f"Ro'yxatdan o'tish raqami: {fund.registration_number}"
    return Decimal("0"), "Davlat ro'yxatidan o'tmagan"


def _score_donation(fund: Fund, reports: list, projects: list) -> tuple[Decimal, str]:
    if fund.donation_url:
        return Decimal("100"), "Xayriya havolasi mavjud"
    return Decimal("0"), "Xayriya havolasi yo'q"


# ---------------------------------------------------------------------------
# Ordered keyword → scoring function map
# Longer / more specific phrases must come BEFORE shorter generic ones.
# ---------------------------------------------------------------------------

FACTOR_SCORING_MAP: list[tuple[str, ScoringFn]] = [
    # Multi-word phrases — most specific first
    ("loyihalar bo'yicha hisobot",       _score_project_reports),
    ("loyihalar muvaffaqiyatli",         _score_project_completion),
    ("xarajatlar tarkibini",             _score_expenses),
    ("donor mablag'",                    _score_donor_income),
    ("benefitsiarlar soni",              _score_beneficiary_count),
    ("benefitsiarlar ro'yxati",          _score_beneficiary_list),
    ("benefitsidarlar soni",             _score_beneficiary_count),
    ("benefitsidarlar ro'yxati",         _score_beneficiary_list),
    ("moliyaviy hisobot",                _score_financial_report),
    ("ijtimoiy tarmoq",                  _score_social),
    ("telegram orqali hisobot",          _score_telegram),
    ("rasmiy veb-sayt",                  _score_website),
    ("davlat ro'yxatidan",               _score_registration),
    ("huquqiy hujjat",                   _score_legal),
    ("xayriya havolasi",                 _score_donation),
    # Single keywords
    ("telegram",                         _score_telegram),
    ("instagram",                        _score_instagram),
    ("ijtimoiy",                         _score_social),
    ("media",                            _score_media),
    ("veb-sayt",                         _score_website),
    ("veb sayt",                         _score_website),
    ("vebsayt",                          _score_website),
    ("website",                          _score_website),
    ("sayt",                             _score_website),
    ("xarajat",                          _score_expenses),
    ("donor",                            _score_donor_income),
    ("mablag'",                          _score_donor_income),
    ("loyiha",                           _score_project_completion),
    ("benefitsiar",                      _score_beneficiary_count),
    ("benefitsiar",                      _score_beneficiary_count),
    ("inn",                              _score_inn),
    ("huquqiy",                          _score_legal),
    ("ro'yxatidan",                      _score_registration),
    ("ro'yxat",                          _score_registration),
    ("qayd",                             _score_registration),
    ("hisobot",                          _score_financial_report),  # catch-all
]

# Factors whose name_uz contains ANY of these words are skipped (manual scoring only)
SKIP_KEYWORDS: tuple[str, ...] = (
    "audit",
    "hamkor",
    "ommaviy tadbirlar",   # "Ommaviy tadbirlar o'tkazish" — can't auto-detect events
    "press-reliz",         # "Yangiliklar va press-relizlar" — can't auto-detect
    "press reliz",
    "yangiliklar va press",
    "intervyu",
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
# Main entry point (background task)
# ---------------------------------------------------------------------------

async def auto_calculate_fund_index(fund_id: UUID) -> None:
    """
    Open a fresh DB session, score all auto-scorable factors for the given
    fund, and persist the weighted index via IndexService.calculate().
    """
    async with AsyncSessionLocal() as db:
        try:
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

            idx_repo = IndexRepository(db)
            factors: list[IndexFactor] = await idx_repo.get_active_factors()

            if not factors:
                log.info("auto_calculate_fund_index: no active factors, skipping")
                return

            scores: list[FactorScoreInput] = []
            skipped: list[str] = []

            for factor in factors:
                name_lower = factor.name_uz.lower()

                if any(kw in name_lower for kw in SKIP_KEYWORDS):
                    skipped.append(factor.name_uz)
                    continue

                scoring_fn = _find_scoring_fn(factor)
                if scoring_fn is None:
                    log.debug(
                        "auto_calculate_fund_index: no scoring fn for '%s', skipping",
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
                    "auto_calculate_fund_index: no auto-scored factors for fund %s", fund_id
                )
                return

            log.info(
                "auto_calculate_fund_index: fund %s — %d factors scored, %d skipped (manual)",
                fund_id, len(scores), len(skipped),
            )

            service = IndexService(db)
            await service.calculate(
                fund_id=fund_id,
                data=IndexCalculateRequest(scores=scores),
            )
            await db.commit()

            log.info("auto_calculate_fund_index: fund %s index updated", fund_id)

        except Exception as exc:
            await db.rollback()
            log.exception(
                "auto_calculate_fund_index: failed for fund %s: %s", fund_id, exc
            )
