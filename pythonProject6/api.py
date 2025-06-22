from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from database import *
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserLogin(BaseModel):
    login: str
    password: str


class UserRegister(BaseModel):
    name: str
    surname: str
    height: float
    weight: float
    gender: bool
    birthday: str
    password: str
    login: str
    photo: str = None


class UserUpdate(BaseModel):
    login: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    height: Optional[float] = None
    birthday: Optional[str] = None
    password: Optional[str] = None


class VerifyPasswordRequest(BaseModel):
    user_id: int
    password: str


class WeightRecordCreate(BaseModel):
    date: str
    weight: float
    notes: Optional[str] = None


class WeightRecordResponse(BaseModel):
    id: int
    date: str
    weight: float
    bmi: Optional[float]
    notes: Optional[str]


class WeightRecordCreate(BaseModel):
    date: str
    weight: float


class RecipeCreateRequest(BaseModel):
    name: str
    callories: float
    photo: Optional[str] = None
    components: str
    steps: str
    squirrels: float = 0
    fats: float = 0
    carbohydrates: float = 0


class RecipeUpdateRequest(BaseModel):
    name: str
    callories: float
    photo: Optional[str] = None
    components: str
    steps: str
    squirrels: float
    fats: float
    carbohydrates: float


class FoodItemCreate(BaseModel):
    nameFood: str
    callories: float
    proteins: float
    fats: float
    carbohydrates: float


class EatingRecordCreate(BaseModel):
    user_id: int
    food_id: int
    date: str
    meal_type: str
    quantity: float
    callories: Optional[float] = None
    proteins: Optional[float] = None
    fats: Optional[float] = None
    carbohydrates: Optional[float] = None


@app.post("/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == user_login.login).first()
    if not user or user.password != user_login.password:
        raise HTTPException(status_code=400, detail="Invalid login or password")

    return {
        "id": user.id,
        "name": user.name,
        "login": user.login,
        "birthday": user.birthday.strftime("%Y-%m-%d") if user.birthday else None,
        "message": "Login successful"
    }


@app.post("/register")
def register(user_register: UserRegister, db: Session = Depends(get_db)):
    try:
        # Проверка, существует ли уже пользователь с таким логином
        existing_user = db.query(User).filter(User.login == user_register.login).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Login already exists")

        # Создание нового пользователя
        new_user = User(
            name=user_register.name,
            surname=user_register.surname,
            height=user_register.height,
            weight=user_register.weight,
            gender=user_register.gender,
            birthday=user_register.birthday,
            password=user_register.password,
            login=user_register.login,
            photo=user_register.photo  # Добавлено поле для фотографии пользователя
        )

        # Добавление нового пользователя в базу данных
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {"message": "Registration successful", "user_id": new_user.id}
    except ValidationError as e:
        logger.error(f"Validation error: {e.json()}")
        raise HTTPException(status_code=422, detail=e.json())
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "name": user.name,
        "login": user.login,
        "birthday": user.birthday.strftime("%Y-%m-%d") if user.birthday else None,
        "height": user.height,
        "surname": user.surname,
        "weight": user.weight,
        "gender": user.gender
    }


@app.put("/users/{user_id}")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Обновляем только переданные поля
        if user_update.login is not None:
            user.login = user_update.login
        if user_update.name is not None:
            user.name = user_update.name
        if user_update.surname is not None:
            user.surname = user_update.surname
        if user_update.height is not None:
            user.height = user_update.height
        if user_update.birthday is not None:
            user.birthday = user_update.birthday
        if user_update.password is not None:
            user.password = user_update.password

        db.commit()

        return {
            "id": user.id,
            "login": user.login,
            "name": user.name,
            "surname": user.surname,
            "height": user.height,
            "birthday": user.birthday
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/users/verify-password")
def verify_password(verify_request: VerifyPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == verify_request.user_id).first()
    if not user:
        return {"is_valid": False}

    if user.password != verify_request.password:
        return {"is_valid": False}

    return {"is_valid": True}


@app.post("/users/{user_id}/weight-records")
def create_weight_record(
        user_id: int,
        record: WeightRecordCreate,
        db: Session = Depends(get_db)
):
    try:
        # Проверяем существование пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Рассчитываем BMI (опционально)
        bmi = None
        if user.height:
            bmi = record.weight / ((user.height / 100) ** 2)

        # Создаем новую запись
        new_record = UserWeightHistory(
            user_id=user_id,
            date=record.date,
            weight=record.weight,
            bmi=bmi,
            notes=record.notes
        )

        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        return {
            "id": new_record.id,
            "date": new_record.date.strftime("%Y-%m-%d"),
            "weight": new_record.weight,
            "bmi": new_record.bmi,
            "notes": new_record.notes
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}/weight-records")
def get_weight_records(
        user_id: int,
        limit: Optional[int] = 100,
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    records = db.query(UserWeightHistory) \
        .filter(UserWeightHistory.user_id == user_id) \
        .order_by(UserWeightHistory.date.desc()) \
        .limit(limit) \
        .all()

    return [{
        "id": r.id,
        "date": r.date.strftime("%Y-%m-%d"),
        "weight": r.weight,
        "bmi": r.bmi,
        "notes": r.notes
    } for r in records]


@app.delete("/weight-records/{record_id}")
def delete_weight_record(
        record_id: int,
        db: Session = Depends(get_db)
):
    record = db.query(UserWeightHistory).filter(UserWeightHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    try:
        db.delete(record)
        db.commit()
        return {"message": "Weight record deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/users/{user_id}/weight-history")
def create_weight_record(
        user_id: int,
        record: WeightRecordCreate,
        db: Session = Depends(get_db)
):
    try:
        # Проверяем существование пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Создаем новую запись в истории
        new_record = UserWeightHistory(
            user_id=user_id,
            date=record.date,
            weight=record.weight
        )

        db.add(new_record)

        # Обновляем текущий вес пользователя
        user.weight = record.weight

        db.commit()

        return {
            "id": new_record.id,
            "date": new_record.date.strftime("%Y-%m-%d"),
            "weight": new_record.weight
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}/weight-history")
def get_weight_history(
        user_id: int,
        db: Session = Depends(get_db)
):
    records = db.query(UserWeightHistory) \
        .filter(UserWeightHistory.user_id == user_id) \
        .order_by(UserWeightHistory.date.desc()) \
        .all()

    return [{
        "id": r.id,
        "date": r.date.strftime("%Y-%m-%d"),
        "weight": r.weight
    } for r in records]


@app.post("/users/{user_id}/recipes")
def create_recipe(
    user_id: int,
    recipe: RecipeCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        # Проверяем существование пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Создаем новый рецепт
        new_recipe = Reciep(
            name=recipe.name,
            callories=recipe.callories if recipe.callories else 0,
            photo=recipe.photo,
            components=recipe.components,
            steps=recipe.steps,
            squirrels=recipe.squirrels if recipe.squirrels else 0,
            fats=recipe.fats if recipe.fats else 0,
            carbohydrates=recipe.carbohydrates if recipe.carbohydrates else 0,
            userID=user_id,
            dateCreate=datetime.now().date()
        )

        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)

        return {"message": "Рецепт успешно создан", "id": new_recipe.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка создания рецепта: {str(e)}")


@app.get("/users/{user_id}/recipes")
def get_user_recipes(user_id: int, db: Session = Depends(get_db)):
    recipes = db.query(Reciep)\
        .filter(Reciep.userID == user_id)\
        .order_by(Reciep.dateCreate.desc())\
        .all()

    return [{
        "id": r.id,
        "name": r.name,
        "photo": r.photo,
        "callories": r.callories,
        "components": r.components,
        "steps": r.steps,
        "squirrels": r.squirrels,
        "fats": r.fats,
        "carbohydrates": r.carbohydrates,
        "dateCreate": r.dateCreate.strftime("%Y-%m-%d")
    } for r in recipes]


@app.put("/recipes/{recipe_id}")
def update_recipe(
    recipe_id: int,
    recipe: RecipeUpdateRequest,
    db: Session = Depends(get_db)
):
    try:
        db_recipe = db.query(Reciep).filter(Reciep.id == recipe_id).first()
        if not db_recipe:
            raise HTTPException(status_code=404, detail="Рецепт не найден")

        db_recipe.name = recipe.name
        db_recipe.callories = recipe.callories
        db_recipe.photo = recipe.photo
        db_recipe.components = recipe.components
        db_recipe.steps = recipe.steps
        db_recipe.squirrels = recipe.squirrels
        db_recipe.fats = recipe.fats
        db_recipe.carbohydrates = recipe.carbohydrates

        db.commit()
        return {"message": "Рецепт успешно обновлен"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    try:
        db_recipe = db.query(Reciep).filter(Reciep.id == recipe_id).first()
        if not db_recipe:
            raise HTTPException(status_code=404, detail="Рецепт не найден")

        db.delete(db_recipe)
        db.commit()
        return {"message": "Рецепт успешно удален"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/food-items")
def create_food_item(food_item: FoodItemCreate, db: Session = Depends(get_db)):
    try:
        # Проверяем, существует ли уже продукт с таким названием
        existing_food = db.query(Food).filter(Food.nameFood == food_item.nameFood).first()
        if existing_food:
            raise HTTPException(status_code=400, detail="Продукт с таким названием уже существует")

        # Создаем новый продукт (без указания id - он сгенерируется автоматически)
        new_food = Food(
            nameFood=food_item.nameFood,
            callories=food_item.callories,
            squirrels=food_item.proteins,
            fats=food_item.fats,
            carbohydrates=food_item.carbohydrates,
            reciepID=None
        )

        db.add(new_food)
        db.commit()
        db.refresh(new_food)

        return {
            "id": new_food.id,
            "nameFood": new_food.nameFood,
            "callories": new_food.callories,
            "proteins": new_food.squirrels,
            "fats": new_food.fats,
            "carbohydrates": new_food.carbohydrates
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/eating-records")
def create_eating_record(record: EatingRecordCreate, db: Session = Depends(get_db)):
    logger.info(f"Received record: {record}")
    try:
        # Проверяем обязательные поля
        if not record.user_id or not record.date or not record.meal_type:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Проверяем существование пользователя
        user = db.query(User).filter(User.id == record.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Для воды (food_id = 0) пропускаем проверку продукта
        food = None
        if record.food_id != 0:
            food = db.query(Food).filter(Food.id == record.food_id).first()
            if not food:
                raise HTTPException(status_code=404, detail="Food not found")

        # Парсим дату (поддерживаем несколько форматов)
        try:
            date_obj = datetime.strptime(record.date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                date_obj = datetime.strptime(record.date, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    date_obj = datetime.strptime(record.date, "%Y-%m-%d")
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=f"Invalid date format: {record.date}")

        # Рассчитываем калории и БЖУ (для воды - нули)
        callories = 0
        proteins = 0
        fats = 0
        carbs = 0

        if food:
            callories = food.callories * record.quantity / 100
            proteins = food.squirrels * record.quantity / 100
            fats = food.fats * record.quantity / 100
            carbs = food.carbohydrates * record.quantity / 100

        # Создаем запись
        new_record = Eating(
            userID=record.user_id,
            foodId=record.food_id,
            date=date_obj,
            callories=callories,
            squirrels=proteins,
            fats=fats,
            carbohydrates=carbs,
            mealType=record.meal_type,
            quantity=record.quantity
        )

        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        return {
            "id": new_record.id,
            "user_id": new_record.userID,
            "food_id": new_record.foodId,
            "date": new_record.date.strftime("%Y-%m-%d %H:%M:%S"),
            "meal_type": new_record.mealType,
            "quantity": new_record.quantity,
            "callories": new_record.callories,
            "proteins": new_record.squirrels,
            "fats": new_record.fats,
            "carbohydrates": new_record.carbohydrates,
            "food_name": food.nameFood if food else "Вода"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating eating record: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/food-items/search")
def search_food_items(query: str = "", db: Session = Depends(get_db)):
    foods = db.query(Food).filter(Food.nameFood.ilike(f"%{query}%")).all()
    return [{
        "id": f.id,
        "nameFood": f.nameFood,
        "callories": f.callories,
        "proteins": f.squirrels,
        "fats": f.fats,
        "carbohydrates": f.carbohydrates
    } for f in foods]


@app.get("/users/{user_id}/eating-records")
def get_eating_records(
        user_id: int,
        date: str,  # Формат "yyyy-MM-dd"
        db: Session = Depends(get_db)
):
    try:
        records = db.query(Eating) \
            .filter(Eating.userID == user_id) \
            .filter(Eating.date >= date + " 00:00:00") \
            .filter(Eating.date <= date + " 23:59:59") \
            .all()

        result = []
        for record in records:
            food_name = ""
            if record.foodId != 0:  # Если это не вода
                food = db.query(Food).filter(Food.id == record.foodId).first()
                food_name = food.nameFood if food else "Неизвестный продукт"

            result.append({
                "id": record.id,
                "user_id": record.userID,
                "food_id": record.foodId,
                "food_name": food_name,
                "date": record.date.strftime("%Y-%m-%d %H:%M:%S"),
                "meal_type": record.mealType,
                "quantity": record.quantity,
                "callories": record.callories,
                "squirrels": record.squirrels,
                "fats": record.fats,
                "carbohydrates": record.carbohydrates
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/eating-records/{record_id}")
def delete_eating_record(record_id: int, db: Session = Depends(get_db)):
    try:
        record = db.query(Eating).filter(Eating.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        db.delete(record)
        db.commit()
        return {"message": "Eating record deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/check-login/{login}")
def check_login_availability(login: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == login).first()
    return {"available": user is None}


@app.get("/recipes")
def get_all_recipes(db: Session = Depends(get_db)):
    recipes = db.query(Reciep).order_by(Reciep.dateCreate.desc()).all()
    return [{
        "id": r.id,
        "name": r.name,
        "photo": r.photo,
        "callories": r.callories,
        "components": r.components,
        "steps": r.steps,
        "squirrels": r.squirrels,
        "fats": r.fats,
        "carbohydrates": r.carbohydrates,
        "dateCreate": r.dateCreate.strftime("%Y-%m-%d")
    } for r in recipes]