from sqlalchemy import create_engine
from models import Base

engine = create_engine("postgresql://postgres:postgres@db:5432/explainitsimple")

Base.metadata.create_all(engine)
