from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://root:***REMOVED***@db:5432/explainitsimple"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
