from dotenv import load_dotenv
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import speech_recognition as sr
from pydub import AudioSegment
import time
from spellchecker import SpellChecker
import re

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Add dictionary for storing recognized texts
recognized_texts = {}

# Initialize spell checking for Russian language
spell = SpellChecker(language='ru')

def correct_spelling(text):
    """Corrects spelling errors in text while preserving punctuation marks"""
    import re
    
    # Regular expression to extract words and punctuation marks
    pattern = r'([^\W\d_]+|\d+|[^\w\s])'
    tokens = re.findall(pattern, text)
    
    corrected_tokens = []
    
    for token in tokens:
        # If it's a punctuation mark or a number, leave it as is
        if not token.isalpha() or len(token) <= 2:
            corrected_tokens.append(token)
            continue
        
        # Check spelling only for words
        if token.lower() in spell:
            corrected_token = token  # Word is correct
        else:
            corrected_token = spell.correction(token.lower())
            if corrected_token:
                # Save the first letter's case
                if token[0].isupper():
                    corrected_token = corrected_token.capitalize()
            else:
                corrected_token = token  # Если исправление не найдено
        
        corrected_tokens.append(corrected_token)
    
    # Restore spaces between words and punctuation marks
    result = ""
    for i, token in enumerate(corrected_tokens):
        # Do not add space before punctuation marks
        if token in ',.!?:;)]}»"' and i > 0:
            result += token
        # Do not add space after opening brackets, quotes, etc.
        elif i > 0 and corrected_tokens[i-1] in '([{«"':
            result += token
        # In other cases, add a space between tokens
        elif i > 0:
            result += " " + token
        else:
            result += token
    
    return result

def add_simple_punctuation(text):
    """
    Добавляет базовую пунктуацию в текст на основе простых правил.
    Не требует внешних библиотек.
    """
    if not text:
        return text
        
    # Разбиваем текст на предложения по возможным границам
    sentences = re.split(r'(?<=[.!?]) +', text)
    result = []
    
    for sentence in sentences:
        # Если предложение уже заканчивается знаком препинания, оставляем как есть
        if sentence and sentence[-1] in '.!?':
            result.append(sentence)
            continue
            
        # Определяем, какой знак препинания добавить в конце
        if re.search(r'\b(кто|что|где|когда|почему|зачем|как|какой|какая|какое|какие|сколько)\b', 
                    sentence.lower()):
            result.append(sentence + '?')
        elif re.search(r'\b(ура|вау|ого|ничего себе|невероятно|потрясающе|круто|здорово|супер)\b', 
                      sentence.lower()):
            result.append(sentence + '!')
        else:
            result.append(sentence + '.')
    
    # Добавляем запятые перед определенными союзами
    text = ' '.join(result)
    text = re.sub(r'\s+(а|но|однако|зато|или|либо|ведь|потому что|поэтому|так как|если|чтобы)\s+', 
                 r', \1 ', text)
    
    # Капитализируем первую букву каждого предложения
    text = re.sub(r'([.!?]\s*)([a-zа-я])', lambda m: m.group(1) + m.group(2).upper(), text)
    
    # Капитализируем первую букву всего текста
    if text and text[0].isalpha():
        text = text[0].upper() + text[1:]
        
    return text

def restore_punctuation_deeppavlov(text):
    """
    Восстанавливает знаки препинания в тексте с помощью модели DeepPavlov.
    Если модель не загружена или произошла ошибка, возвращает текст с простой пунктуацией.
    """
    global deeppavlov_loaded, punctuation_model
    
    # Если текст пустой, возвращаем его как есть
    if not text:
        return text
    
    # Пробуем загрузить модель DeepPavlov, если она еще не загружена
    if not deeppavlov_loaded:
        try:
            logger.info("Загрузка модели DeepPavlov для восстановления пунктуации...")
            from deeppavlov import build_model, configs
            
            # Загружаем модель для восстановления пунктуации
            punctuation_model = build_model("punctuation_restore", download=True)
            deeppavlov_loaded = True
            logger.info("Модель DeepPavlov успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели DeepPavlov: {e}")
            # Если не удалось загрузить модель, используем простую функцию
            return add_simple_punctuation(text)
    
    # Используем модель для восстановления пунктуации
    try:
        # DeepPavlov ожидает список предложений
        result = punctuation_model([text])
        if result and len(result) > 0:
            return result[0]
        else:
            return add_simple_punctuation(text)
    except Exception as e:
        logger.error(f"Ошибка при восстановлении пунктуации с DeepPavlov: {e}")
        # В случае ошибки используем простую функцию
        return add_simple_punctuation(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send greeting message when /start command is issued"""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! 👋\nПросто отправь мне голосовое сообщение, и я преобразую его в текст."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message when /help command is issued"""
    help_text = """
    🤖 How to use the bot:
    1. Simply record and send me a voice message.
    2. I will download it, process it, and send you the recognized text.
    
    ⚠️ *Currently, I best understand voice messages in Russian.*
    """
    await update.message.reply_markdown(help_text)

def convert_ogg_to_wav(ogg_file_path):
    """Converts an audio file from .ogg (Telegram) format to .wav (for SpeechRecognition)"""
    wav_file_path = ogg_file_path.replace(".ogg", ".wav")
    
    # Load .ogg file
    audio = AudioSegment.from_ogg(ogg_file_path)
    # Export to .wav with necessary parameters
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
        # Use Google Web Speech API
        # Specify language: 'ru-RU' for Russian
        text = recognizer.recognize_google(audio_data, language='ru-RU')
        return text
    except sr.UnknownValueError:
        return "Не удалось распознать речь. Аудио может быть пустым или неразборчивым."
    except sr.RequestError as e:
        return f"Ошибка сервиса распознавания; {e}"

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает входящие голосовые сообщения"""
    # Check if message and voice message exist
    if not update.message or not update.message.voice:
        return
        
    # Get file information
    voice_file = await update.message.voice.get_file()
    user_id = update.message.from_user.id
    file_id = voice_file.file_id
    ogg_file_path = f"temp_voice_{user_id}_{file_id}.ogg"
    wav_file_path = None
    
    # Upload file to Telegram server
    await voice_file.download_to_drive(ogg_file_path)
    await update.message.reply_text("🎙️ Audio received! Processing...")
    
    try:
        # Convert .ogg to .wav
        wav_file_path = convert_ogg_to_wav(ogg_file_path)
        
        # Recognize speech
        recognized_text = speech_to_text(wav_file_path)
        
        # Correct spelling errors
        corrected_text = correct_spelling(recognized_text)
        
        # Восстанавливаем пунктуацию с помощью DeepPavlov
        corrected_text = restore_punctuation_deeppavlov(corrected_text)
        
        # Generate unique ID for text
        text_id = f"text_{user_id}_{int(time.time())}"
        
        # Save text in dictionary
        recognized_texts[text_id] = corrected_text
        
        # Создаем кнопку "Скопировать текст" с коротким ID вместо полного текста
        keyboard = [
            [InlineKeyboardButton("📋 Скопировать текст", callback_data=f"copy:{text_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем результат пользователю с кнопкой
        await update.message.reply_text(
            f"🎙️ Распознанный текст:\n{corrected_text}", 
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
    # Check if message and voice message exist
    if not update.channel_post or not update.channel_post.voice:
        return
    
    # Get channel information
    channel_id = update.channel_post.chat.id
    channel_title = update.channel_post.chat.title
    message_id = update.channel_post.message_id
    
    # Get file information
    voice_file = await update.channel_post.voice.get_file()
    file_id = voice_file.file_id
    ogg_file_path = f"temp_voice_channel_{channel_id}_{file_id}.ogg"
    wav_file_path = None
    
    # Log received message
    logger.info(f"Получено голосовое сообщение из канала  '{channel_title}' (ID: {channel_id})")
    
    try:
        # Download file
        await voice_file.download_to_drive(ogg_file_path)
        
        # Конвертируем .ogg в .wav
        wav_file_path = convert_ogg_to_wav(ogg_file_path)
        
        # Распознаем речь
        recognized_text = speech_to_text(wav_file_path)
        
        # Исправляем орфографические ошибки
        corrected_text = correct_spelling(recognized_text)
        
        # Восстанавливаем пунктуацию с помощью DeepPavlov
        corrected_text = restore_punctuation_deeppavlov(corrected_text)
        
        # Генерируем уникальный ID для текста
        text_id = f"text_{channel_id}_{int(time.time())}"
        
        # Сохраняем текст в словаре
        recognized_texts[text_id] = corrected_text
        
        # Создаем кнопку "Скопировать текст" с коротким ID вместо полного текста
        keyboard = [
            [InlineKeyboardButton("📋 Скопировать текст", callback_data=f"copy:{text_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем результат в канал как ответ на голосовое сообщение с кнопкой
        await context.bot.send_message(
            chat_id=channel_id,
            text=f"🎙️ Распознанный текст:\n{corrected_text}",
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

deeppavlov_loaded = False
punctuation_model = None

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
