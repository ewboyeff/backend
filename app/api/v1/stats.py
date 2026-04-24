from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.models.application import Application
from app.models.complaint import Complaint, ComplaintStatus
from app.models.fund import Fund
from app.models.index import FundIndex, IndexGrade
from app.models.project import Project
from app.models.review import Review
from app.models.user import User, UserRole

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/public")
async def public_stats(db: AsyncSession = Depends(get_db)):
    from app.models.fund import FundStatus

    total_funds = (
        await db.execute(
            select(func.count()).select_from(Fund).where(Fund.status == FundStatus.active)
        )
    ).scalar_one()

    verified_funds = (
        await db.execute(
            select(func.count()).select_from(Fund).where(Fund.is_verified == True)
        )
    ).scalar_one()

    total_projects = (await db.execute(select(func.count()).select_from(Project))).scalar_one()

    beneficiaries_row = (
        await db.execute(select(func.coalesce(func.sum(Project.beneficiaries_count), 0)))
    ).scalar_one()

    return {
        "total_funds": total_funds,
        "verified_funds": verified_funds,
        "total_projects": total_projects,
        "total_beneficiaries": int(beneficiaries_row),
    }


@router.get(
    "/dashboard",
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Counts
    total_funds = (await db.execute(select(func.count()).select_from(Fund))).scalar_one()
    total_projects = (await db.execute(select(func.count()).select_from(Project))).scalar_one()
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    total_applications = (await db.execute(select(func.count()).select_from(Application))).scalar_one()

    pending_reviews = (
        await db.execute(
            select(func.count()).select_from(Review).where(Review.is_approved == False)
        )
    ).scalar_one()

    pending_complaints = (
        await db.execute(
            select(func.count()).select_from(Complaint).where(
                Complaint.status == ComplaintStatus.pending
            )
        )
    ).scalar_one()

    # Funds by grade
    grade_rows = (
        await db.execute(
            select(FundIndex.grade, func.count().label("cnt"))
            .group_by(FundIndex.grade)
        )
    ).all()
    funds_by_grade = {row.grade: row.cnt for row in grade_rows}

    # Recent 5 funds
    recent_result = await db.execute(
        select(Fund).order_by(Fund.created_at.desc()).limit(5)
    )
    recent_funds = recent_result.scalars().all()

    recent_funds_data = []
    for f in recent_funds:
        grade = f.indexes.grade if f.indexes else IndexGrade.unrated
        overall = float(f.indexes.overall_score) if f.indexes else 0
        recent_funds_data.append({
            "id": str(f.id),
            "name_uz": f.name_uz,
            "logo_initials": f.logo_initials,
            "logo_color": f.logo_color,
            "category": f.category.name_uz if f.category else "",
            "grade": grade,
            "overall": round(overall),
            "is_active": f.is_active,
            "slug": f.slug,
        })

    return {
        "total_funds": total_funds,
        "total_projects": total_projects,
        "total_users": total_users,
        "total_applications": total_applications,
        "pending_reviews": pending_reviews,
        "pending_complaints": pending_complaints,
        "funds_by_grade": {
            "platinum": funds_by_grade.get(IndexGrade.platinum, 0),
            "gold": funds_by_grade.get(IndexGrade.gold, 0),
            "silver": funds_by_grade.get(IndexGrade.silver, 0),
            "bronze": funds_by_grade.get(IndexGrade.bronze, 0),
            "unrated": funds_by_grade.get(IndexGrade.unrated, 0),
        },
        "recent_funds": recent_funds_data,
    }
