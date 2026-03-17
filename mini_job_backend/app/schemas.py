from pydantic import BaseModel, Field

class JobBase(BaseModel):
    title: str = Field(..., min_length=3)
    company: str = Field(..., min_length=2)
    salary: float = Field(..., gt=0)
    description: str = Field(..., min_length=5)

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: int

    class Config:
        from_attributes = True