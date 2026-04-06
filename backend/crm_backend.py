# crm_backend.py - РАБОЧАЯ ВЕРСИЯ С ГЕОЛОКАЦИЕЙ
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Enum, Text, Float, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import logging
import enum
import os

# Конфигурация
DATABASE_URL = "sqlite:///./crm.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Часовой пояс Екатеринбурга (UTC+5)
YEKATERINBURG_OFFSET = timedelta(hours=5)

def get_yekaterinburg_time():
    """Возвращает текущее время в Екатеринбурге (UTC+5)"""
    return datetime.utcnow() + YEKATERINBURG_OFFSET

def format_yekaterinburg_time(dt):
    """Форматирует время для отображения"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return None

# Enums
class MessageStatus(str, enum.Enum):
    NEW = "new"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Модели БД
class MessageModel(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, default="max")
    chat_id = Column(String, index=True)
    user_id = Column(String, index=True)
    user_name = Column(String)
    text = Column(Text)
    photos = Column(JSON, default=list)
    status = Column(Enum(MessageStatus), default=MessageStatus.NEW)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    created_at = Column(DateTime, default=get_yekaterinburg_time)
    updated_at = Column(DateTime, default=get_yekaterinburg_time, onupdate=get_yekaterinburg_time)
    notes = Column(Text, nullable=True)
    assigned_to = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    response_time = Column(Integer, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    # Поля для геолокации
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_address = Column(String, nullable=True)

# Создание таблиц (обновляем существующую таблицу)
def upgrade_database():
    """Обновление базы данных - добавление полей для геолокации"""
    try:
        # Проверяем существование колонок и добавляем если их нет
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('messages')]
        
        if 'latitude' not in columns:
            with engine.connect() as conn:
                conn.execute('ALTER TABLE messages ADD COLUMN latitude FLOAT')
                conn.execute('ALTER TABLE messages ADD COLUMN longitude FLOAT')
                conn.execute('ALTER TABLE messages ADD COLUMN location_address TEXT')
                conn.commit()
                logger.info("✅ Добавлены поля для геолокации")
    except Exception as e:
        logger.warning(f"⚠️ Обновление базы данных: {e}")

Base.metadata.create_all(bind=engine)
upgrade_database()

# Pydantic схемы
class MessageCreate(BaseModel):
    source: str = "max"
    chat_id: str
    user_id: str
    user_name: str
    text: str
    photos: List[str] = []
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_address: Optional[str] = None
    received_at: Optional[datetime] = None

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    chat_id: str
    user_id: str
    user_name: str
    text: str
    photos: List[str]
    status: MessageStatus
    priority: Priority
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: List[str] = []
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_address: Optional[str] = None

class MessageUpdate(BaseModel):
    status: Optional[MessageStatus] = None
    priority: Optional[Priority] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None

# FastAPI приложение
app = FastAPI(title="MAX CRM API", version="2.0")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_maps_links(lat, lon):
    """Генерирует ссылки на карты"""
    if not lat or not lon:
        return None
    return {
        "yandex": f"https://yandex.ru/maps/?pt={lon},{lat}&z=17&l=map",
        "google": f"https://www.google.com/maps?q={lat},{lon}",
        "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=17/{lat}/{lon}"
    }

# API Endpoints
@app.post("/api/messages", response_model=MessageResponse)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    """Создание нового сообщения с поддержкой геолокации"""
    
    # Определяем время получения (Екатеринбург)
    if message.received_at:
        received_at = message.received_at
        logger.info(f"📅 Используем присланное время: {received_at}")
    else:
        received_at = get_yekaterinburg_time()
        logger.info(f"📅 Используем текущее время Екатеринбурга: {received_at}")
    
    logger.info(f"📨 Получено сообщение от {message.user_name}")
    logger.info(f"📷 Фото: {len(message.photos)} шт.")
    logger.info(f"🕐 Время Екатеринбург: {format_yekaterinburg_time(received_at)}")
    
    if message.latitude and message.longitude:
        logger.info(f"📍 Геолокация: {message.latitude}, {message.longitude}")
        maps = generate_maps_links(message.latitude, message.longitude)
        if maps:
            logger.info(f"   Яндекс.Карты: {maps['yandex']}")
    
    db_message = MessageModel(
        source=message.source,
        chat_id=message.chat_id,
        user_id=message.user_id,
        user_name=message.user_name,
        text=message.text,
        photos=message.photos,
        created_at=received_at,
        latitude=message.latitude,
        longitude=message.longitude,
        location_address=message.location_address
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

@app.get("/api/messages", response_model=List[MessageResponse])
def list_messages(
    status: Optional[MessageStatus] = None,
    priority: Optional[Priority] = None,
    chat_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    search: Optional[str] = None,
    has_location: Optional[bool] = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Список сообщений с фильтрацией"""
    query = db.query(MessageModel)
    
    if status:
        query = query.filter(MessageModel.status == status)
    if priority:
        query = query.filter(MessageModel.priority == priority)
    if chat_id:
        query = query.filter(MessageModel.chat_id == chat_id)
    if assigned_to:
        query = query.filter(MessageModel.assigned_to == assigned_to)
    if search:
        query = query.filter(
            (MessageModel.text.contains(search)) |
            (MessageModel.user_name.contains(search))
        )
    if has_location is not None:
        if has_location:
            query = query.filter(MessageModel.latitude.isnot(None))
        else:
            query = query.filter(MessageModel.latitude.is_(None))
    
    if status != MessageStatus.CANCELLED:
        query = query.filter(MessageModel.status != MessageStatus.CANCELLED)
    
    messages = query.order_by(
        MessageModel.priority.desc(),
        MessageModel.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return messages

@app.get("/api/messages/{message_id}", response_model=MessageResponse)
def get_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(MessageModel).filter(MessageModel.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@app.patch("/api/messages/{message_id}", response_model=MessageResponse)
def update_message(
    message_id: int,
    update: MessageUpdate,
    db: Session = Depends(get_db)
):
    message = db.query(MessageModel).filter(MessageModel.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    for field, value in update.dict(exclude_unset=True).items():
        setattr(message, field, value)
    
    if update.status == MessageStatus.COMPLETED and not message.resolved_at:
        message.resolved_at = get_yekaterinburg_time()
        if message.created_at:
            message.response_time = int((message.resolved_at - message.created_at).total_seconds())
    
    message.updated_at = get_yekaterinburg_time()
    db.commit()
    db.refresh(message)
    return message

@app.delete("/api/messages/last")
def delete_last_message(chat_id: str, db: Session = Depends(get_db)):
    message = db.query(MessageModel).filter(
        MessageModel.chat_id == chat_id
    ).order_by(MessageModel.created_at.desc()).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="No messages found")
    
    if message.status == MessageStatus.NEW:
        message.status = MessageStatus.CANCELLED
        db.commit()
        return {"status": "cancelled", "message_id": message.id}
    
    raise HTTPException(status_code=400, detail="Cannot cancel message in current status")

@app.get("/api/statistics")
def get_statistics(db: Session = Depends(get_db)):
    now = get_yekaterinburg_time()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=now.weekday())
    
    total = db.query(MessageModel).count()
    
    by_status = {}
    for status in MessageStatus:
        count = db.query(MessageModel).filter(MessageModel.status == status).count()
        by_status[status.value] = count
    
    by_priority = {}
    for priority in Priority:
        count = db.query(MessageModel).filter(MessageModel.priority == priority).count()
        by_priority[priority.value] = count
    
    avg_response = db.query(func.avg(MessageModel.response_time)).filter(
        MessageModel.response_time.isnot(None)
    ).scalar() or 0
    
    messages_today = db.query(MessageModel).filter(
        MessageModel.created_at >= today_start
    ).count()
    
    messages_week = db.query(MessageModel).filter(
        MessageModel.created_at >= week_start
    ).count()
    
    # Статистика по геолокации
    messages_with_location = db.query(MessageModel).filter(
        MessageModel.latitude.isnot(None)
    ).count()
    
    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "average_response_time": round(float(avg_response), 2),
        "messages_today": messages_today,
        "messages_this_week": messages_week,
        "messages_with_location": messages_with_location
    }

@app.get("/api/messages/location/{message_id}")
def get_message_location(message_id: int, db: Session = Depends(get_db)):
    """Получить геолокацию сообщения со ссылками на карты"""
    message = db.query(MessageModel).filter(MessageModel.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if not message.latitude or not message.longitude:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return {
        "id": message.id,
        "latitude": message.latitude,
        "longitude": message.longitude,
        "address": message.location_address,
        "maps": generate_maps_links(message.latitude, message.longitude)
    }

@app.get("/api/debug/photos")
def debug_photos(db: Session = Depends(get_db)):
    """Отладочный эндпоинт для проверки фото в БД"""
    messages = db.query(MessageModel).filter(
        MessageModel.photos != []
    ).limit(10).all()
    
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "user_name": msg.user_name,
            "photo_count": len(msg.photos),
            "photos": msg.photos,
            "created_at": format_yekaterinburg_time(msg.created_at),
            "has_location": msg.latitude is not None
        })
    
    return {
        "total_messages_with_photos": len(messages),
        "messages": result
    }

@app.get("/api/health")
def health_check():
    now = get_yekaterinburg_time()
    return {
        "status": "ok",
        "timestamp": now.isoformat(),
        "timezone": "Asia/Yekaterinburg (UTC+5)",
        "local_time": format_yekaterinburg_time(now)
    }

if __name__ == "__main__":
    import uvicorn
    from sqlalchemy import inspect
    
    now = get_yekaterinburg_time()
    print("=" * 50)
    print("🚀 Запуск CRM Backend на http://localhost:5001")
    print("📚 Документация API: http://localhost:5001/docs")
    print(f"🕐 Время Екатеринбурга: {format_yekaterinburg_time(now)}")
    print("📍 Поддержка геолокации: Включена")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=5001,
        reload=False,
        log_level="info"
    )