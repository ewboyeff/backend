from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String)
    salary = Column(Float)
    description = Column(String)