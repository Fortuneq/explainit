from sqlalchemy import create_engine
from models import Base

engine = create_engine("postgresql://root:***REMOVED***@db:6432/explainitsimple")

Base.metadata.create_all(engine)
