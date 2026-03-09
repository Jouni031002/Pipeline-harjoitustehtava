from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/urls"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# List of tables in the database
tables = [
    'urls',
    'users',
    'user_urls'
]

# Print table names
print("Tables in the database:")
for table in tables:
    print(table)