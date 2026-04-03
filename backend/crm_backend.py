# crm_backend.py - ФИНАЛЬНАЯ ВЕРСИЯ
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Enum, Text, func
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
    photos = Column(JSON, default=list)  # URL фото
    status = Column(Enum(MessageStatus), default=MessageStatus.NEW)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    notes = Column(Text, nullable=True)
    assigned_to = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    response_time = Column(Integer, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Pydantic схемы
class MessageCreate(BaseModel):
    source: str = "max"
    chat_id: str
    user_id: str
    user_name: str
    text: str
    photos: List[str] = []
    received_at: datetime

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

# API Endpoints
@app.post("/api/messages", response_model=MessageResponse)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    """Создание нового сообщения"""
    
    logger.info(f"Получено сообщение от {message.user_name}")
    logger.info(f"Фото: {len(message.photos)} шт.")
    
    db_message = MessageModel(
        source=message.source,
        chat_id=message.chat_id,
        user_id=message.user_id,
        user_name=message.user_name,
        text=message.text,
        photos=message.photos,
        created_at=message.received_at
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
    
    if status != MessageStatus.CANCELLED:
        query = query.filter(MessageModel.status != MessageStatus.CANCELLED)
    
    return query.order_by(
        MessageModel.priority.desc(),
        MessageModel.created_at.desc()
    ).offset(offset).limit(limit).all()

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
        message.resolved_at = datetime.now()
        if message.created_at:
            message.response_time = int((message.resolved_at - message.created_at).total_seconds())
    
    db.commit()
    db.refresh(message)
    return message

@app.get("/api/statistics")
def get_statistics(db: Session = Depends(get_db)):
    now = datetime.now()
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
    
    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "average_response_time": round(float(avg_response), 2),
        "messages_today": messages_today,
        "messages_this_week": messages_week
    }

@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 Запуск CRM Backend на http://localhost:5001")
    print("📚 Документация API: http://localhost:5001/docs")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=5001,
        reload=False,
        log_level="info"
    )