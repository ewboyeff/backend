"""
Seed script — run once to populate initial data.

Usage (from charity-index-backend/ directory):
    python scripts/seed.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from decimal import Decimal

# Make sure app package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.category import Category
from app.models.index import IndexFactor, IndexType
from app.models.region import Region
from app.models.user import User, UserRole

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

CATEGORIES = [
    {"name_uz": "Ta'lim", "slug": "talim"},
    {"name_uz": "Sog'liqni saqlash", "slug": "sogligni-saqlash"},
    {"name_uz": "Bolalar", "slug": "bolalar"},
    {"name_uz": "Ekologiya", "slug": "ekologiya"},
    {"name_uz": "Kambag'alikni qisqartirish", "slug": "kambagalikni-qisqartirish"},
    {"name_uz": "Ijtimoiy ko'mak", "slug": "ijtimoiy-komak"},
]

REGIONS = [
    {"name_uz": "Toshkent shahri", "code": "TSH"},
    {"name_uz": "Toshkent viloyati", "code": "TO"},
    {"name_uz": "Samarqand", "code": "SA"},
    {"name_uz": "Farg'ona", "code": "FA"},
    {"name_uz": "Buxoro", "code": "BU"},
    {"name_uz": "Namangan", "code": "NA"},
    {"name_uz": "Andijon", "code": "AN"},
    {"name_uz": "Qashqadaryo", "code": "QA"},
    {"name_uz": "Surxondaryo", "code": "SU"},
    {"name_uz": "Xorazm", "code": "XO"},
    {"name_uz": "Navoiy", "code": "NV"},
    {"name_uz": "Jizzax", "code": "JI"},
    {"name_uz": "Sirdaryo", "code": "SI"},
    {"name_uz": "Qoraqalpog'iston", "code": "QR"},
]

INDEX_FACTORS = [
    # Transparency (shaffoflik) — umumiy 100%
    {
        "index_type": IndexType.transparency,
        "name_uz": "Moliyaviy hisobotlar",
        "weight": Decimal("25.00"),
        "order": 1,
    },
    {
        "index_type": IndexType.transparency,
        "name_uz": "Sarflash tafsiloti",
        "weight": Decimal("20.00"),
        "order": 2,
    },
    {
        "index_type": IndexType.transparency,
        "name_uz": "Loyiha natijalari",
        "weight": Decimal("20.00"),
        "order": 3,
    },
    {
        "index_type": IndexType.transparency,
        "name_uz": "Audit o'tkazilgan",
        "weight": Decimal("20.00"),
        "order": 4,
    },
    {
        "index_type": IndexType.transparency,
        "name_uz": "Donor ma'lumotlari",
        "weight": Decimal("15.00"),
        "order": 5,
    },
    # Openness (ochiqlik) — umumiy 100%
    {
        "index_type": IndexType.openness,
        "name_uz": "Rasmiy veb-sayt",
        "weight": Decimal("20.00"),
        "order": 1,
    },
    {
        "index_type": IndexType.openness,
        "name_uz": "Ijtimoiy tarmoq",
        "weight": Decimal("20.00"),
        "order": 2,
    },
    {
        "index_type": IndexType.openness,
        "name_uz": "Media ko'rinishi",
        "weight": Decimal("15.00"),
        "order": 3,
    },
    {
        "index_type": IndexType.openness,
        "name_uz": "Murojaat imkoniyati",
        "weight": Decimal("20.00"),
        "order": 4,
    },
    {
        "index_type": IndexType.openness,
        "name_uz": "Yangiliklar chastotasi",
        "weight": Decimal("25.00"),
        "order": 5,
    },
    # Trust (ishonch) — umumiy 100%
    {
        "index_type": IndexType.trust,
        "name_uz": "Rasmiy ro'yxatdan o'tgan",
        "weight": Decimal("25.00"),
        "order": 1,
    },
    {
        "index_type": IndexType.trust,
        "name_uz": "Faoliyat davomiyligi",
        "weight": Decimal("20.00"),
        "order": 2,
    },
    {
        "index_type": IndexType.trust,
        "name_uz": "Foydalanuvchi reytingi",
        "weight": Decimal("20.00"),
        "order": 3,
    },
    {
        "index_type": IndexType.trust,
        "name_uz": "Shikoyatlar tarixi",
        "weight": Decimal("20.00"),
        "order": 4,
    },
    {
        "index_type": IndexType.trust,
        "name_uz": "Xalqaro hamkorlar",
        "weight": Decimal("15.00"),
        "order": 5,
    },
]

ADMIN_USER = {
    "email": "admin@charityindex.uz",
    "password": "admin2025",
    "full_name": "Admin",
    "role": UserRole.admin,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def seed_categories(db) -> None:
    for data in CATEGORIES:
        result = await db.execute(
            select(Category).where(Category.slug == data["slug"])
        )
        if result.scalar_one_or_none() is None:
            db.add(Category(**data))
            print(f"  + Category: {data['name_uz']}")
        else:
            print(f"  ~ Category already exists: {data['name_uz']}")


async def seed_regions(db) -> None:
    for data in REGIONS:
        result = await db.execute(
            select(Region).where(Region.code == data["code"])
        )
        if result.scalar_one_or_none() is None:
            db.add(Region(**data))
            print(f"  + Region: {data['name_uz']}")
        else:
            print(f"  ~ Region already exists: {data['name_uz']}")


async def seed_index_factors(db) -> None:
    for data in INDEX_FACTORS:
        result = await db.execute(
            select(IndexFactor).where(
                IndexFactor.index_type == data["index_type"],
                IndexFactor.name_uz == data["name_uz"],
            )
        )
        if result.scalar_one_or_none() is None:
            db.add(IndexFactor(**data))
            print(f"  + Factor [{data['index_type'].value}]: {data['name_uz']}")
        else:
            print(f"  ~ Factor already exists: {data['name_uz']}")


async def seed_admin(db) -> None:
    result = await db.execute(
        select(User).where(User.email == ADMIN_USER["email"])
    )
    if result.scalar_one_or_none() is None:
        db.add(
            User(
                email=ADMIN_USER["email"],
                password_hash=hash_password(ADMIN_USER["password"]),
                full_name=ADMIN_USER["full_name"],
                role=ADMIN_USER["role"],
            )
        )
        print(f"  + Admin user: {ADMIN_USER['email']}")
    else:
        print(f"  ~ Admin user already exists: {ADMIN_USER['email']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    print("\n=== Charity Index — Seed Script ===\n")

    async with AsyncSessionLocal() as db:
        print("[1/4] Seeding categories...")
        await seed_categories(db)

        print("\n[2/4] Seeding regions...")
        await seed_regions(db)

        print("\n[3/4] Seeding index factors...")
        await seed_index_factors(db)

        print("\n[4/4] Seeding admin user...")
        await seed_admin(db)

        await db.commit()

    print("\n=== Done! ===\n")


if __name__ == "__main__":
    asyncio.run(main())
