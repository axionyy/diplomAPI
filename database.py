from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Float, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Eating(Base):
    __tablename__ = 'eating'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    userID = Column(Integer, ForeignKey('users.id'), nullable=False)
    foodId = Column(Integer, ForeignKey('food.id'), nullable=False)
    callories = Column(Float, nullable=True)
    squirrels = Column(Float, nullable=True)
    fats = Column(Float, nullable=True)
    carbohydrates = Column(Float, nullable=True)
    date = Column(DateTime, nullable=False)
    mealType = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)

    user = relationship("User", back_populates="eatings")
    food = relationship("Food", back_populates="eatings")


class Food(Base):
    __tablename__ = 'food'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    nameFood = Column(String(50), nullable=False)
    callories = Column(Float, nullable=True)
    squirrels = Column(Float, nullable=True)
    fats = Column(Float, nullable=True)
    carbohydrates = Column(Float, nullable=True)
    reciepID = Column(Integer, ForeignKey('reciep.id'), nullable=True)

    eatings = relationship("Eating", back_populates="food")
    reciep = relationship("Reciep", back_populates="foods")


class Reciep(Base):
    __tablename__ = 'reciep'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(50), nullable=False)
    callories = Column(Float, nullable=False)
    photo = Column(Text, nullable=True)
    userID = Column(Integer, ForeignKey('users.id'), nullable=False)
    dateCreate = Column(Date, nullable=False)
    components = Column(Text, nullable=False)
    steps = Column(Text, nullable=True)
    squirrels = Column(Float, nullable=True)
    fats = Column(Float, nullable=True)
    carbohydrates = Column(Float, nullable=True)

    user = relationship("User", back_populates="recieps")
    foods = relationship("Food", back_populates="reciep")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    gender = Column(Boolean, nullable=False)
    birthday = Column(Date, nullable=False)
    password = Column(String(50), nullable=False)
    login = Column(String(50), nullable=False)
    photo = Column(Text, nullable=True)

    eatings = relationship("Eating", back_populates="user")
    recieps = relationship("Reciep", back_populates="user")
    weight_history = relationship("UserWeightHistory", back_populates="user",
                                  cascade="all, delete-orphan")


class UserWeightHistory(Base):
    __tablename__ = 'user_weight_history'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False)
    weight = Column(Float, nullable=False)

    user = relationship("User", back_populates="weight_history")


# Создание подключения к базе данных
engine = create_engine("postgresql://diplom_v91y_user:MUmARmEkA6z4FZ5fIpE3NkDmTkluMe0L@dpg-d1c7ocuuk2gs73af1ah0-a.oregon-postgres.render.com:5432/diplom_v91y", echo=True)


# Создание таблиц
Base.metadata.create_all(engine)
