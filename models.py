import datetime
from sqlalchemy import create_engine, Column, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Roast(Base):
    __tablename__ = 'roasts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DateTime, nullable=False, default=datetime.datetime.now)
    sec_from_start = Column(Text, nullable=False, default=datetime.datetime.now)
    temperature_f = Column(Text, nullable=False)
    bean_info = Column(Text)
    first_crack_start_time = Column(Float)
    first_crack_start_temp = Column(Float)
    second_crack_start_time = Column(Float)
    second_crack_start_temp = Column(Float)
    tasting_comments = Column(Text)


    def __repr__(self):
        return (f"<Roast(id={self.id}, start_time='{self.start_time}', "
                f"bean_info='{self.bean_info[:20] if self.bean_info else 'N/A'}...')>")


DATABASE_URL = "sqlite:///data/roast_data.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
