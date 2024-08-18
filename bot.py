from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import instaloader
import logging
import requests
from io import BytesIO

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Ваш токен, полученный от BotFather
token = '7060931880:AAEB_s6wexQONWE1Z7oiM8dgs7o-Lm4v0Rg'

# Создаем инстанс Instaloader
L = instaloader.Instaloader()

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Начать", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Привет! Нажми "Начать", чтобы отправить ссылку на фото или видео из Instagram, и я сохраню их для тебя.', 
        reply_markup=reply_markup
    )

# Функция для обработки нажатия кнопки
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Отправь мне ссылку на фото или видео из Instagram.")

# Функция для обработки сообщений
async def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    chat_id = update.message.chat_id
    logging.info(f'Received message from chat_id: {chat_id}')
    
    if 'instagram.com' in url:
        try:
            shortcode = url.split('/')[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            
            media_files = []

            # Добавляем основное изображение или видео
            if post.is_video:
                media_files.append(post.video_url)
            else:
                media_files.append(post.url)

            # Проверяем, если пост содержит несколько файлов (карусель)
            for node in post.get_sidecar_nodes():
                if node.is_video:
                    media_files.append(node.video_url)
                else:
                    # Добавляем только уникальные изображения
                    if node.display_url not in media_files:
                        media_files.append(node.display_url)

            for media_url in media_files:
                try:
                    response = requests.get(media_url, timeout=20)
                    
                    if response.status_code == 200:
                        media_stream = BytesIO(response.content)
                        media_stream.seek(0)

                        # Определяем тип медиа
                        if "video" in response.headers.get('Content-Type'):
                            # Отправляем видео в чат
                            await context.bot.send_video(chat_id=chat_id, video=media_stream, caption="Вот ваше видео!")
                        else:
                            # Отправляем фото в чат
                            await context.bot.send_photo(chat_id=chat_id, photo=media_stream, caption="Вот ваше фото!")
                        
                        media_stream.close()
                    else:
                        await update.message.reply_text(f'Не удалось загрузить медиафайл из Instagram: {media_url}')

                except requests.exceptions.RequestException as e:
                    await update.message.reply_text(f'Ошибка при загрузке медиафайла: {e}')
        except Exception as e:
            await update.message.reply_text(f'Ошибка: {e}')
    else:
        await update.message.reply_text('Это не похоже на ссылку из Instagram.')

def main():
    # Создаем объект Application с использованием токена
    application = Application.builder().token(token).build()
    
    # Регистрация обработчиков команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))  # Обработчик для нажатий на кнопки
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
