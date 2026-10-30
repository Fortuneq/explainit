import os

from sqlalchemy import create_engine
from models import Base

engine = create_engine(os.environ["DATABASE_URL"])

Base.metadata.create_all(engine)
