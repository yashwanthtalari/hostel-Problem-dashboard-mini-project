from sqlalchemy import Column, Integer, String
from database import Base

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String)
    room_number = Column(String)
    category = Column(String)
    description = Column(String)
    status = Column(String, default="Open")
