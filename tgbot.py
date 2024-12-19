import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from supabase import create_client, Client  # Предполагается, что вы добавите эту функцию позже
from dotenv import load_dotenv
import openai

# Загрузка переменных окружения
load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
openai_base_url = os.getenv('OPENAI_BASE_URL')

openai = openai.Client(api_key=openai_api_key, base_url=openai_base_url)

def classify(content):
    profile = "Applied AI Engineer @ Yandex"
    
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"You are a helpful assistant. Classify, is this resource relevant to my profile: {profile}. If it is, return only '1', otherwise return only '0'. Do not return anything else."}, {"role": "user", "content": content}],
        max_tokens=1,
        temperature=0
    ).choices[0].message.content
    
    return response == '1'

# Инициализация Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(supabase_url, supabase_service_role_key)

# Инициализация бота
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

async def monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('Обработка команды /monthly')
    
    # Получение данных из Supabase
    response = supabase.table('producthunt').select('microsum, link').execute()
    logging.debug(f'Ответ от Supabase: {response}')
    
    # Проверка на наличие ошибок в ответе
    if not response.data:  # Предположим, что пустой data означает ошибку
        logging.error('Ошибка при получении данных из Supabase: данные отсутствуют')
        await update.message.reply_text('Произошла ошибка при получении данных.')
        return
    
    data = response.data
    logging.debug(f'Полученные данные: {data}')
    messages = []
    
    for item in data:
        microsum = item.get('microsum')
        link = item.get('link')
        
        # Проверка через функцию classify
        classification_result = classify(microsum)
        logging.debug(f'Результат классификации для "{microsum}": {classification_result}')
        if classification_result:
            message = f"Сводка: {microsum}\nСсылка: {link}"
            messages.append(message)
    
    if messages:
        await update.message.reply_text('\n\n'.join(messages))
    else:
        await update.message.reply_text('Нет доступных данных для отображения.')

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    monthly_handler = CommandHandler('monthly', monthly)
    application.add_handler(monthly_handler)

    logging.info('Бот запущен и готов к работе.')
    application.run_polling()

if __name__ == '__main__':
    main()
