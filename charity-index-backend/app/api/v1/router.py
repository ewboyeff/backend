from fastapi import APIRouter

from app.api.v1 import applications, auth, categories, complaints, funds, indexes, news, partners, projects, reports, research, reviews, stats, uploads, users

api_router = APIRouter(prefix="/api/v1")

# Auth
api_router.include_router(auth.router)

# Funds
api_router.include_router(funds.router)

# Indexes
api_router.include_router(indexes.router)

# Reviews — POST/GET under /funds/{fund_id}/reviews
api_router.include_router(reviews.router)
# Reviews — approve/delete under /reviews/{review_id}
api_router.include_router(reviews.reviews_admin_router)

# Complaints — POST under /funds/{fund_id}/complaints
api_router.include_router(complaints.router)
# Complaints — GET list + PUT under /complaints
api_router.include_router(complaints.complaints_router)

# News
api_router.include_router(news.router)

# Users (admin)
api_router.include_router(users.router)

# Categories & Regions
api_router.include_router(categories.router)

# Applications (hamkorlik murojaatlari)
api_router.include_router(applications.router)

# File uploads
api_router.include_router(uploads.router)

# Partners (hamkorlar)
api_router.include_router(partners.router)

# Projects (admin CRUD)
api_router.include_router(projects.router)

# Financial Reports
api_router.include_router(reports.router)

# Dashboard Stats (admin)
api_router.include_router(stats.router)

# Research / Tadqiqot page settings
api_router.include_router(research.router)
