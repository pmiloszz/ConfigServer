# scripts/test_db.py
import os
from sqlmodel import SQLModel, Session, select
from app.models import Flag
from app.db import engine

def run():
    print("Using DATABASE_URL:", os.getenv("DATABASE_URL", "sqlite:///./flags.db"))
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        f = Flag(app="demo", env="dev", key="feature_x", value=True)
        s.add(f)
        s.commit()
        s.refresh(f)
        print("Inserted id:", f.id)
        rows = s.exec(select(Flag)).all()
        print("Rows count:", len(rows))
        for r in rows:
            print(r)

if __name__ == "__main__":
    run()