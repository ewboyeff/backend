from app.db.session import async_session
from app.db.models import Application
import logging

async def save_application(data: dict) -> bool:
    try:
        async with async_session() as session:
            app = Application(
                full_name=data.get("full_name"),
                phone=data.get("phone"),
                direction=data.get("direction"),
                technologies=data.get("technologies"),
                portfolio_url=data.get("portfolio"),
                telegram_username=data.get("telegram_username"),
                telegram_user_id=data.get("telegram_user_id"),
            )
            session.add(app)
            await session.commit()
            return True
    except Exception as e:
        logging.error(f"Database error while saving application: {e}")
        return False

async def get_recent_applications(limit: int = 10):
    from sqlalchemy import select
    try:
        async with async_session() as session:
            stmt = select(Application).order_by(Application.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()
    except Exception as e:
        logging.error(f"Database error while fetching applications: {e}")
        return []
