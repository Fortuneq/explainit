from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class GenerationLog(Base):
    __tablename__ = "generation_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    user_name = Column(String)
    question = Column(Text)
    response = Column(Text)
