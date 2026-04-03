# bot/max_bot.py - ФИНАЛЬНАЯ ВЕРСИЯ С ПРИВЕТСТВИЕМ
import requests
import time
import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional
from io import BytesIO
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
MAX_API_URL = "https://platform-api.max.ru"
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
CRM_API_URL = os.getenv("CRM_API_URL", "http://localhost:5001/api/messages")

# Настраиваемое приветственное сообщение
WELCOME_MESSAGE = """📢 Данный бот предназначен для фиксации нанесенных надписей по распространению наркотиков

📸 Пожалуйста, отправьте фото с местом нанесения надписи
📍 Укажите адрес в описании к фото
📝 Ваше сообщение будет передано в соответствующие органы

Спасибо за активную гражданскую позицию! 🙏"""

# Создаем директорию для сохранения фото
PHOTOS_DIR = Path("downloaded_photos")
PHOTOS_DIR.mkdir(exist_ok=True)

if not BOT_TOKEN:
    logger.error("❌ Токен бота не установлен!")
    logger.error("Установите переменную окружения MAX_BOT_TOKEN")
    exit(1)

HEADERS = {
    "Authorization": BOT_TOKEN,
    "Content-Type": "application/json"
}

class MaxBot:
    def __init__(self):
        self.marker = None
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def get_updates(self, timeout: int = 30, limit: int = 100) -> List[Dict]:
        """Получение обновлений через Long Polling"""
        params = {"timeout": timeout, "limit": limit}
        if self.marker:
            params["marker"] = self.marker
        
        try:
            response = self.session.get(
                f"{MAX_API_URL}/updates",
                params=params,
                timeout=timeout + 5
            )
            
            if response.status_code == 200:
                data = response.json()
                updates = data.get("updates", [])
                new_marker = data.get("marker")
                if new_marker:
                    self.marker = new_marker
                logger.info(f"📨 Получено {len(updates)} обновлений")
                return updates
            else:
                logger.error(f"Ошибка API MAX: {response.status_code}")
                if response.text:
                    logger.error(f"Ответ: {response.text[:200]}")
                return []
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return []
    
    def send_message_to_user(self, user_id: int, text: str, keyboard: Dict = None) -> bool:
        """Отправка сообщения пользователю"""
        url = f"{MAX_API_URL}/messages?user_id={user_id}"
        payload = {"text": text}
        if keyboard:
            payload["attachments"] = [{
                "type": "inline_keyboard",
                "payload": keyboard
            }]
        
        try:
            response = self.session.post(url, json=payload)
            if response.status_code == 200:
                logger.info(f"✅ Сообщение отправлено пользователю {user_id}")
                return True
            else:
                logger.error(f"❌ Ошибка отправки: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False
    
    def download_and_upload_photo(self, file_id: str, save_local: bool = True) -> Optional[Dict]:
        """
        Загрузка фото с локальным сохранением для отладки
        """
        try:
            # Шаг 1: Получаем содержимое файла через API MAX
            logger.info(f"📥 Скачиваем файл {file_id}...")
            file_response = self.session.get(
                f"{MAX_API_URL}/files/{file_id}",
                timeout=30
            )
            
            if file_response.status_code != 200:
                logger.error(f"❌ Ошибка получения файла: {file_response.status_code}")
                logger.error(f"Ответ: {file_response.text[:200]}")
                return None
            
            file_content = file_response.content
            logger.info(f"✅ Файл скачан: {len(file_content)} байт")
            
            # Локальное сохранение для отладки
            local_path = None
            if save_local and file_content:
                local_path = PHOTOS_DIR / f"{file_id}.jpg"
                with open(local_path, 'wb') as f:
                    f.write(file_content)
                logger.info(f"💾 Файл сохранен локально: {local_path}")
            
            # Шаг 2: Запрашиваем URL для загрузки в MAX
            logger.info(f"📤 Запрос URL для загрузки...")
            upload_response = self.session.post(
                f"{MAX_API_URL}/uploads?type=image"
            )
            
            if upload_response.status_code != 200:
                logger.error(f"❌ Ошибка получения URL: {upload_response.status_code}")
                logger.error(f"Ответ: {upload_response.text[:200]}")
                return None
            
            upload_data = upload_response.json()
            upload_url = upload_data.get("url")
            
            if not upload_url:
                logger.error("❌ Нет URL в ответе")
                logger.error(f"Ответ: {upload_data}")
                return None
            
            logger.info(f"✅ Получен URL для загрузки: {upload_url[:80]}...")
            
            # Шаг 3: Загружаем файл в MAX
            files = {'data': (f"{file_id}.jpg", BytesIO(file_content), 'image/jpeg')}
            upload_result = requests.post(
                upload_url,
                files=files
            )
            
            if upload_result.status_code == 200:
                result = upload_result.json()
                photo_url = result.get("url") or result.get("link")
                if photo_url:
                    logger.info(f"✅ Фото загружено в MAX")
                    logger.info(f"   URL: {photo_url[:80]}...")
                    return {
                        "url": photo_url,
                        "token": None,
                        "local_path": str(local_path) if local_path else None
                    }
                else:
                    logger.warning(f"⚠️ Неожиданный ответ MAX: {result}")
                    return None
            else:
                logger.error(f"❌ Ошибка загрузки в MAX: {upload_result.status_code}")
                logger.error(f"Ответ: {upload_result.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке фото: {e}", exc_info=True)
            return None
    
    def save_to_crm(self, message_data: Dict) -> bool:
        """Сохранение сообщения в CRM"""
        try:
            logger.info(f"📤 Отправка в CRM: {json.dumps(message_data, indent=2, default=str, ensure_ascii=False)}")
            response = requests.post(
                CRM_API_URL,
                json=message_data,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info("✅ Сообщение сохранено в CRM")
                return True
            else:
                logger.error(f"❌ Ошибка CRM: {response.status_code}")
                logger.error(f"Ответ: {response.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка отправки в CRM: {e}")
            return False
    
    def process_message_created(self, update: Dict):
        """Обработка нового сообщения с детальным логированием"""
        logger.info("=" * 60)
        
        # Получаем сообщение из update
        message = update.get("message", {})
        
        # Получаем данные отправителя
        sender = message.get("sender", {})
        target_user_id = sender.get("user_id")
        sender_name = sender.get("name", "Unknown")
        
        # Получаем текст сообщения
        body = message.get("body", {})
        text = body.get("text", "") or message.get("text", "")
        
        # Проверяем команду /start
        if text == "/start":
            logger.info(f"👋 Пользователь {sender_name} (ID: {target_user_id}) запустил бота")
            self.send_message_to_user(target_user_id, WELCOME_MESSAGE)
            return
        
        # Логируем структуру сообщения для отладки
        logger.info("📨 СТРУКТУРА СООБЩЕНИЯ:")
        logger.info(json.dumps(message, indent=2, default=str, ensure_ascii=False))
        
        # Пробуем найти вложения в разных местах
        attachments = []
        
        # Вариант 1: В body
        if body.get("attachments"):
            attachments = body.get("attachments", [])
            logger.info(f"📎 Найдены attachments в body: {len(attachments)}")
        
        # Вариант 2: Прямо в message
        if not attachments and message.get("attachments"):
            attachments = message.get("attachments", [])
            logger.info(f"📎 Найдены attachments в message: {len(attachments)}")
        
        # Вариант 3: В поле media
        if not attachments and message.get("media"):
            media = message.get("media", {})
            if media.get("attachments"):
                attachments = media.get("attachments", [])
                logger.info(f"📎 Найдены attachments в media: {len(attachments)}")
        
        # Получаем chat_id
        recipient = message.get("recipient", {})
        chat_id = recipient.get("chat_id", "")
        
        logger.info(f"👤 Отправитель: {sender_name} (ID: {target_user_id})")
        logger.info(f"💬 Чат ID: {chat_id}")
        logger.info(f"📝 Текст: {text[:100] if text else 'Нет текста'}")
        logger.info(f"📎 Найдено вложений: {len(attachments)}")
        
        # Обрабатываем каждое вложение
        photo_urls = []
        photo_tokens = []
        
        for idx, attachment in enumerate(attachments):
            att_type = attachment.get("type")
            payload = attachment.get("payload", {})
            
            logger.info(f"📎 Вложение #{idx}: type={att_type}")
            logger.info(f"   payload: {json.dumps(payload, ensure_ascii=False)}")
            
            if att_type in ["image", "photo"]:
                # Пробуем разные варианты получения ID файла
                file_id = (
                    payload.get("file_id") or 
                    payload.get("id") or 
                    payload.get("fileId") or
                    payload.get("file") or
                    payload.get("file_id_str")
                )
                
                if file_id:
                    logger.info(f"📷 Найден file_id: {file_id}")
                    result = self.download_and_upload_photo(file_id, save_local=True)
                    if result and result.get("url"):
                        photo_urls.append(result["url"])
                        logger.info(f"✅ Фото успешно обработано")
                        if result.get('local_path'):
                            logger.info(f"   Локально сохранено: {result['local_path']}")
                    else:
                        logger.warning(f"⚠️ Не удалось обработать фото: {file_id}")
                else:
                    logger.warning(f"⚠️ Не удалось найти file_id в payload")
                    logger.warning(f"   Доступные ключи: {list(payload.keys())}")
                    
                    # Если есть прямой URL в payload
                    if payload.get("url"):
                        logger.info(f"   Найден прямой URL: {payload.get('url')}")
                        photo_urls.append(payload.get("url"))
        
        # Получаем timestamp
        timestamp = update.get("timestamp", datetime.now().timestamp())
        if isinstance(timestamp, (int, float)):
            received_at = datetime.fromtimestamp(timestamp / 1000).isoformat()
        else:
            received_at = datetime.now().isoformat()
        
        # Формируем данные для CRM
        crm_payload = {
            "source": "max",
            "chat_id": str(chat_id) if chat_id else "",
            "user_id": str(target_user_id) if target_user_id else "",
            "user_name": sender_name,
            "text": text,
            "photos": photo_urls,
            "photo_tokens": photo_tokens,
            "received_at": received_at
        }
        
        logger.info(f"📤 Итоговые данные для CRM:")
        logger.info(f"   Фото: {len(photo_urls)} шт.")
        if photo_urls:
            logger.info(f"   Первое фото: {photo_urls[0][:80]}...")
        
        # Сохраняем в CRM
        if self.save_to_crm(crm_payload):
            reply_text = "✅ Ваше сообщение принято! Спасибо за бдительность."
            if photo_urls:
                reply_text += f" 📷 Получено фото: {len(photo_urls)} шт."
            if target_user_id:
                self.send_message_to_user(target_user_id, reply_text)
    
    def run(self):
        """Основной цикл"""
        logger.info("=" * 60)
        logger.info("🤖 Бот запущен")
        logger.info(f"🔗 MAX API: {MAX_API_URL}")
        logger.info(f"💾 CRM API: {CRM_API_URL}")
        logger.info(f"📁 Директория для фото: {PHOTOS_DIR.absolute()}")
        logger.info("=" * 60)
        
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    update_type = update.get("update_type")
                    logger.info(f"📌 Тип обновления: {update_type}")
                    
                    if update_type == "message_created":
                        self.process_message_created(update)
                    else:
                        logger.info(f"Другое обновление: {json.dumps(update, indent=2, ensure_ascii=False)}")
                
                time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("👋 Остановка бота...")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле: {e}", exc_info=True)
                time.sleep(5)

if __name__ == "__main__":
    # Проверяем наличие токена
    if not BOT_TOKEN:
        print("\n" + "=" * 60)
        print("❌ ОШИБКА: Токен бота не установлен!")
        print("Установите переменную окружения MAX_BOT_TOKEN")
        print("\nПример:")
        print("  Windows: set MAX_BOT_TOKEN=ваш_токен")
        print("  Linux/Mac: export MAX_BOT_TOKEN=ваш_токен")
        print("=" * 60)
        exit(1)
    
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК БОТА")
    print(f"📁 Фото будут сохраняться в: {PHOTOS_DIR.absolute()}")
    print("=" * 60)
    print("\n📢 Приветственное сообщение:")
    print(WELCOME_MESSAGE)
    print("=" * 60 + "\n")
    
    bot = MaxBot()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")