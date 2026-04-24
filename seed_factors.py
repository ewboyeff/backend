"""
Seed default IndexFactor records into the database.
Run once: python seed_factors.py
"""
import asyncio
from decimal import Decimal
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.index import IndexFactor, IndexType

FACTORS = [
    # ── Shaffoflik (Transparency) — 40% of Overall ──────────────────────────
    # weights must sum to 100 within this group
    dict(index_type=IndexType.transparency, name_uz="Yillik moliyaviy hisobot",        name_ru="Годовой финансовый отчёт",      name_en="Annual financial report",         weight=Decimal("30"), order=1),
    dict(index_type=IndexType.transparency, name_uz="Mustaqil audit xulosasi",          name_ru="Независимое аудиторское заключение", name_en="Independent audit report",    weight=Decimal("25"), order=2),
    dict(index_type=IndexType.transparency, name_uz="Davlat ro'yxatidan o'tganlik",     name_ru="Государственная регистрация",   name_en="State registration",             weight=Decimal("20"), order=3),
    dict(index_type=IndexType.transparency, name_uz="Maqsadli sarflanish hisoboti",     name_ru="Отчёт о целевом расходовании",  name_en="Targeted expenditure report",    weight=Decimal("25"), order=4),

    # ── Ochiqlik (Openness) — 30% of Overall ────────────────────────────────
    dict(index_type=IndexType.openness,     name_uz="Rasmiy veb-sayt mavjudligi",       name_ru="Наличие официального сайта",    name_en="Official website availability",  weight=Decimal("25"), order=1),
    dict(index_type=IndexType.openness,     name_uz="Ijtimoiy tarmoqlardagi faollik",   name_ru="Активность в социальных сетях", name_en="Social media activity",          weight=Decimal("20"), order=2),
    dict(index_type=IndexType.openness,     name_uz="Aloqa ma'lumotlarining to'liqligi",name_ru="Полнота контактной информации", name_en="Contact information completeness",weight=Decimal("20"), order=3),
    dict(index_type=IndexType.openness,     name_uz="Loyihalar va natijalar hisoboti",  name_ru="Отчёт о проектах и результатах",name_en="Projects and results reporting", weight=Decimal("35"), order=4),

    # ── Ishonchlilik (Trust) — 30% of Overall ───────────────────────────────
    dict(index_type=IndexType.trust,        name_uz="Foydalanuvchilar baholash ko'rsatkichi", name_ru="Показатель пользовательских оценок", name_en="User rating score",    weight=Decimal("35"), order=1),
    dict(index_type=IndexType.trust,        name_uz="Shikoyatlar va nizolar darajasi",  name_ru="Уровень жалоб и споров",        name_en="Complaints and dispute rate",    weight=Decimal("30"), order=2),
    dict(index_type=IndexType.trust,        name_uz="Hamkorlar va akkreditatsiya",      name_ru="Партнёры и аккредитация",       name_en="Partners and accreditation",     weight=Decimal("20"), order=3),
    dict(index_type=IndexType.trust,        name_uz="Tashkilot faoliyat muddati",       name_ru="Срок деятельности организации", name_en="Years of operation",             weight=Decimal("15"), order=4),
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        existing = (await session.execute(select(IndexFactor))).scalars().all()
        if existing:
            print(f"[seed] {len(existing)} ta omil allaqachon mavjud — o'tkazib yuborildi.")
            return

        for data in FACTORS:
            session.add(IndexFactor(**data, is_active=True))

        await session.commit()
        print(f"[seed] {len(FACTORS)} ta omil muvaffaqiyatli qo'shildi.")
        for f in FACTORS:
            print(f"  [{f['index_type'].value}] {f['name_uz']} — {f['weight']}%")


if __name__ == "__main__":
    asyncio.run(seed())
