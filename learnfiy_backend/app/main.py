from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.auth import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    authenticate_admin,
    create_access_token,
    get_current_admin_user,
    hash_password,
    verify_password,
)
from app.database import Base, SessionLocal, engine, get_db
from app.models import Course, Enrollment, User
from app.schemas import (
    AdminLoginRequest,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    EnrollmentCreate,
    MessageResponse,
    TokenResponse,
    UserResponse,
)


def _find_unique_index_name(indexes: list[dict], column_names: list[str]) -> str | None:
    for index in indexes:
        if index.get("unique") and index.get("column_names") == column_names:
            return index["name"]
    return None


def _quote_identifier(identifier: str) -> str:
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def ensure_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "users" in table_names:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        user_unique_constraints = {
            constraint["name"] for constraint in inspector.get_unique_constraints("users")
        }
        user_email_index = _find_unique_index_name(
            inspector.get_indexes("users"),
            ["email"],
        )
        with engine.begin() as connection:
            if "phone" not in user_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN phone VARCHAR(30) NOT NULL DEFAULT ''"
                )
            if "password_hash" not in user_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"
                )
            if "is_admin" not in user_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE"
                )
            if "created_at" not in user_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE users "
                    "ADD COLUMN created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()"
                )
            if "uq_users_email" not in user_unique_constraints:
                if user_email_index is not None:
                    connection.exec_driver_sql(
                        "ALTER TABLE users "
                        f"ADD CONSTRAINT uq_users_email UNIQUE USING INDEX {_quote_identifier(user_email_index)}"
                    )
                else:
                    connection.exec_driver_sql(
                        "ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email)"
                    )

    if "enrollments" in table_names:
        enrollment_unique_constraints = {
            constraint["name"] for constraint in inspector.get_unique_constraints("enrollments")
        }
        enrollment_unique_index = _find_unique_index_name(
            inspector.get_indexes("enrollments"),
            ["user_id", "course_id"],
        )
        if "uq_user_course" not in enrollment_unique_constraints:
            with engine.begin() as connection:
                if enrollment_unique_index is not None:
                    connection.exec_driver_sql(
                        "ALTER TABLE enrollments "
                        f"ADD CONSTRAINT uq_user_course UNIQUE USING INDEX {_quote_identifier(enrollment_unique_index)}"
                    )
                else:
                    connection.exec_driver_sql(
                        "ALTER TABLE enrollments "
                        "ADD CONSTRAINT uq_user_course UNIQUE (user_id, course_id)"
                    )


def seed_data() -> None:
    db = SessionLocal()
    try:
        should_commit = False

        if not db.scalar(select(Course.id).limit(1)):
            db.add_all(
                [
                    Course(
                        title="Python Basics",
                        description="Learn Python from scratch with practical examples.",
                        video_url="https://example.com/python-basics",
                    ),
                    Course(
                        title="FastAPI Essentials",
                        description="Build fast and modern APIs with FastAPI.",
                        video_url="https://example.com/fastapi-essentials",
                    ),
                    Course(
                        title="SQL for Beginners",
                        description="Understand SQL queries, joins, and database basics.",
                        video_url="https://example.com/sql-for-beginners",
                    ),
                ]
            )
            should_commit = True

        if not db.scalar(select(User.id).where(User.is_admin.is_(False)).limit(1)):
            db.add_all(
                [
                    User(
                        full_name="Alice Johnson",
                        email="alice@example.com",
                        phone="+998901112233",
                    ),
                    User(
                        full_name="Bob Smith",
                        email="bob@example.com",
                        phone="+998901234567",
                    ),
                ]
            )
            should_commit = True

        if should_commit:
            db.commit()
    finally:
        db.close()


def seed_admin() -> None:
    db = SessionLocal()
    try:
        admin_user = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
        admin_password_hash = hash_password(ADMIN_PASSWORD)

        if admin_user is None:
            admin_user = User(
                full_name="Learnfiy Admin",
                email=ADMIN_EMAIL,
                phone="N/A",
                password_hash=admin_password_hash,
                is_admin=True,
            )
            db.add(admin_user)
            try:
                db.commit()
                return
            except IntegrityError:
                db.rollback()
                admin_user = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
                if admin_user is None:
                    raise

        should_commit = False
        if not admin_user.is_admin:
            admin_user.is_admin = True
            should_commit = True
        if admin_user.password_hash is None or not verify_password(
            ADMIN_PASSWORD,
            admin_user.password_hash,
        ):
            admin_user.password_hash = admin_password_hash
            should_commit = True
        if not admin_user.phone.strip():
            admin_user.phone = "N/A"
            should_commit = True

        if should_commit:
            db.commit()
    finally:
        db.close()


def get_course_or_404(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    seed_data()
    seed_admin()
    yield


app = FastAPI(
    title="Learnfiy API",
    description="A compact backend API for the Learnfiy online learning platform.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "User", "description": "Public user-facing endpoints."},
        {"name": "Admin", "description": "Admin authentication and management endpoints."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_router = APIRouter(prefix="/auth", tags=["Admin"])
public_courses_router = APIRouter(tags=["User"])
enrollment_router = APIRouter(tags=["User"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


@public_courses_router.get("/courses", response_model=list[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    return db.scalars(select(Course).order_by(Course.id)).all()


@auth_router.post("/login", response_model=TokenResponse)
def login_admin(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin_user = authenticate_admin(db, payload.email, payload.password)
    if admin_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(admin_user))


@admin_router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    course = Course(
        title=payload.title,
        description=payload.description,
        video_url=payload.video_url,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@admin_router.put("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    course = get_course_or_404(db, course_id)
    course.title = payload.title
    course.description = payload.description
    course.video_url = payload.video_url
    db.commit()
    db.refresh(course)
    return course


@admin_router.delete("/courses/{course_id}", response_model=MessageResponse)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    course = get_course_or_404(db, course_id)
    db.delete(course)
    db.commit()
    return MessageResponse(message="Course deleted successfully")


@public_courses_router.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    return get_course_or_404(db, course_id)


@admin_router.get("/users", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    return db.scalars(select(User).order_by(User.id)).all()


@enrollment_router.post(
    "/enroll",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def enroll_user(payload: EnrollmentCreate, db: Session = Depends(get_db)):
    course = db.get(Course, payload.course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        user = User(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
        )
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            user = db.scalar(select(User).where(User.email == payload.email))
            if user is None:
                raise
    if user is not None:
        user.full_name = payload.full_name
        user.phone = payload.phone

    existing_enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == payload.course_id,
        )
    )
    if existing_enrollment is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already enrolled in this course",
        )

    db.add(Enrollment(user_id=user.id, course_id=payload.course_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already enrolled in this course",
        ) from None
    return MessageResponse(message="Enrollment created successfully")


app.include_router(auth_router)
app.include_router(public_courses_router)
app.include_router(enrollment_router)
app.include_router(admin_router)
