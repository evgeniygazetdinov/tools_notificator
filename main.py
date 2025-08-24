from dotenv import load_dotenv
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import speech_recognition as sr
from pydub import AudioSegment
import time

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Добавляем словарь для хранения распознанных текстов
recognized_texts = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение при команде /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! 👋\nПросто отправь мне голосовое сообщение, и я преобразую его в текст."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет справку при команде /help"""
    help_text = """
    🤖 Как пользоваться ботом:
    1. Просто запиши и отправь мне голосовое сообщение.
    2. Я скачаю его, обработаю и отправлю тебе распознанный текст.
    
    ⚠️ *Пока что я лучше всего понимаю голосовые на русском языке.*
    """
    await update.message.reply_markdown(help_text)

def convert_ogg_to_wav(ogg_file_path):
    """Конвертирует аудиофайл из формата .ogg (Telegram) в .wav (для SpeechRecognition)"""
    wav_file_path = ogg_file_path.replace(".ogg", ".wav")
    
    # Загружаем .ogg файл
    audio = AudioSegment.from_ogg(ogg_file_path)
    # Экспортируем в .wav с нужными параметрами
    audio.export(wav_file_path, format="wav", parameters=["-ac", "1", "-ar", "16000"])
    
    return wav_file_path

def speech_to_text(audio_file_path):
    """Распознает речь из аудиофайла и возвращает текст"""
    recognizer = sr.Recognizer()
    
    with sr.AudioFile(audio_file_path) as source:
        # Adjust for ambient noise and read the entire audio file
        recognizer.adjust_for_ambient_noise(source)
        audio_data = recognizer.record(source)
    
    try:
        # Используем Google Web Speech API
        # Указываем язык: 'ru-RU' для русского
        text = recognizer.recognize_google(audio_data, language='ru-RU')
        return text
    except sr.UnknownValueError:
        return "Не удалось распознать речь. Аудио может быть пустым или неразборчивым."
    except sr.RequestError as e:
        return f"Ошибка сервиса распознавания; {e}"

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает входящие голосовые сообщения"""
    # Проверяем, есть ли сообщение и голосовое сообщение
    if not update.message or not update.message.voice:
        return
        
    # Получаем информацию о файле
    voice_file = await update.message.voice.get_file()
    user_id = update.message.from_user.id
    file_id = voice_file.file_id
    ogg_file_path = f"temp_voice_{user_id}_{file_id}.ogg"
    wav_file_path = None
    
    # Скачиваем файл
    await voice_file.download_to_drive(ogg_file_path)
    await update.message.reply_text("🎙️ Аудио получено! Обрабатываю...")
    
    try:
        # Конвертируем .ogg в .wav
        wav_file_path = convert_ogg_to_wav(ogg_file_path)
        
        # Распознаем речь
        recognized_text = speech_to_text(wav_file_path)
        
        # Генерируем уникальный ID для текста
        text_id = f"text_{user_id}_{int(time.time())}"
        
        # Сохраняем текст в словаре
        recognized_texts[text_id] = recognized_text
        
        # Создаем кнопку "Скопировать текст" с коротким ID вместо полного текста
        keyboard = [
            [InlineKeyboardButton("📋 Скопировать текст", callback_data=f"copy:{text_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем результат пользователю с кнопкой
        await update.message.reply_text(
            f"🎙️ Распознанный текст:\n{recognized_text}", 
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке аудио: {e}")
        await update.message.reply_text("😕 Произошла ошибка при обработке аудио. Попробуй еще раз.")
    
    finally:
        # Удаляем временные файлы
        if os.path.exists(ogg_file_path):
            os.remove(ogg_file_path)
        if wav_file_path and os.path.exists(wav_file_path):
            os.remove(wav_file_path)

async def handle_channel_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает голосовые сообщения из канала"""
    # Проверяем, есть ли голосовое сообщение
    if not update.channel_post or not update.channel_post.voice:
        return
    
    # Получаем информацию о канале
    channel_id = update.channel_post.chat.id
    channel_title = update.channel_post.chat.title
    message_id = update.channel_post.message_id
    
    # Получаем информацию о файле
    voice_file = await update.channel_post.voice.get_file()
    file_id = voice_file.file_id
    ogg_file_path = f"temp_voice_channel_{channel_id}_{file_id}.ogg"
    wav_file_path = None
    
    # Логируем получение сообщения
    logger.info(f"Получено голосовое сообщение из канала '{channel_title}' (ID: {channel_id})")
    
    try:
        # Скачиваем файл
        await voice_file.download_to_drive(ogg_file_path)
        
        # Конвертируем .ogg в .wav
        wav_file_path = convert_ogg_to_wav(ogg_file_path)
        
        # Распознаем речь
        recognized_text = speech_to_text(wav_file_path)
        
        # Генерируем уникальный ID для текста
        text_id = f"text_{channel_id}_{int(time.time())}"
        
        # Сохраняем текст в словаре
        recognized_texts[text_id] = recognized_text
        
        # Создаем кнопку "Скопировать текст" с коротким ID вместо полного текста
        keyboard = [
            [InlineKeyboardButton("📋 Скопировать текст", callback_data=f"copy:{text_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем результат в канал как ответ на голосовое сообщение с кнопкой
        await context.bot.send_message(
            chat_id=channel_id,
            text=f"🎙️ Распознанный текст:\n{recognized_text}",
            reply_to_message_id=message_id,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке аудио из канала: {e}")
        await context.bot.send_message(
            chat_id=channel_id,
            text="😕 Произошла ошибка при обработке аудио.",
            reply_to_message_id=message_id
        )
    
    finally:
        # Удаляем временные файлы
        if os.path.exists(ogg_file_path):
            os.remove(ogg_file_path)
        if wav_file_path and os.path.exists(wav_file_path):
            os.remove(wav_file_path)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения, сообщая что бот принимает только голосовые"""
    await update.message.reply_text("🎤 Я принимаю только голосовые сообщения. Пожалуйста, запишите и отправьте голосовое сообщение.")

async def handle_other_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает все остальные типы сообщений"""
    await update.message.reply_text("🎤 Я принимаю только голосовые сообщения. Пожалуйста, запишите и отправьте голосовое сообщение.")

async def handle_copy_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие кнопки "Скопировать текст" """
    query = update.callback_query
    await query.answer()
    text_id = query.data.split(":")[1]
    text = recognized_texts.get(text_id)
    if text:
        await query.edit_message_text(text=f"Текст скопирован в буфер обмена: {text}")
    else:
        await query.edit_message_text(text="Текст не найден.")

def main():
    """Запускает бота"""
    # Создаем Application и передаем ему токен бота
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Настраиваем дополнительное логирование
    logging.getLogger('telegram').setLevel(logging.DEBUG)
    logging.getLogger('httpx').setLevel(logging.DEBUG)
    
    # Добавляем обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Добавляем обработчик для голосовых сообщений из канала (должен быть перед обычным обработчиком голосовых)
    channel_handler = MessageHandler(
        filters.ChatType.CHANNEL & filters.VOICE, 
        handle_channel_voice_message
    )
    application.add_handler(channel_handler)
    logger.info("Зарегистрирован обработчик для голосовых сообщений из канала")
    
    # Добавляем обработчик для обычных голосовых сообщений
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    
    # Добавляем обработчик для текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Добавляем обработчик для всех остальных типов сообщений
    application.add_handler(MessageHandler(~filters.VOICE & ~filters.COMMAND, handle_other_messages))
    
    # Добавляем обработчик для кнопки "Скопировать текст"
    application.add_handler(CallbackQueryHandler(handle_copy_text, pattern="^copy:"))
    
    # Добавляем обработчик для всех обновлений (для отладки)
    async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(f"Получено обновление типа: {update.update_id}")
        if update.channel_post:
            logger.info(f"Получено сообщение из канала: {update.channel_post.chat.title}")
            if update.channel_post.voice:
                logger.info("Сообщение содержит голосовое сообщение")
    
    application.add_handler(MessageHandler(filters.ALL, log_update), group=999)
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    print("Запуск бота...")
    main()
