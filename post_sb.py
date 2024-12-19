import os
import requests
import openai
from supabase import create_client, Client
import logging
from bs4 import BeautifulSoup

# Настройка логирования
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()

# Инициализация OpenAI и Supabase
openai_api_key = os.getenv('OPENAI_API_KEY')
openai_base_url = os.getenv('OPENAI_BASE_URL')
supabase_url = os.getenv('SUPABASE_URL')
supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
supabase_service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

openai = openai.Client(api_key=openai_api_key, base_url=openai_base_url)
supabase: Client = create_client(supabase_url, supabase_service_role_key)

# Чтение ссылок из файла
logging.info('Чтение ссылок из файла links.txt')
with open('links.txt', 'r') as file:
    links = file.readlines()

# Функция для получения содержимого сайта
def fetch_website_content(url):
    logging.debug(f'Получение содержимого сайта: {url}')
    try:
        response = requests.get(url)
        response.raise_for_status()
        logging.debug(f'Успешно получено содержимое сайта: {url}')
        
        # Извлечение текста из HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text()
        
        return text_content
    except requests.RequestException as e:
        logging.error(f'Ошибка при получении содержимого сайта {url}: {e}')
        return None

# Функция для суммаризации содержимого
def summarize_content(content):
    logging.debug('Суммаризация содержимого')
    # Используем OpenAI для суммаризации
    summary = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a helpful assistant. Summarize the content of the website in 500 characters or less."}, {"role": "user", "content": content}],
        max_tokens=1300
    ).choices[0].message.content
    logging.debug('Суммаризация завершена')
    return summary

# Функция для создания микро-саммари
def create_micro_summary(content):
    logging.debug('Создание микро-саммари')
    micro_summary = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a helpful assistant. Summarize the content of the website in 3 sentences or less."}, {"role": "user", "content": content}],
        max_tokens=1000
    ).choices[0].message.content
    
    logging.debug('Микро-саммари создано')
    return micro_summary

# Основной процесс
for link in links:
    link = link.strip()
    logging.info(f'Обработка ссылки: {link}')
    content = fetch_website_content(link)
    if content:
        summary = summarize_content(content)
        micro_summary = create_micro_summary(content)
        # Сохранение в Supabase
        data = {
            "full_content": content,
            "sum": summary,
            "microsum": micro_summary,
            "link": link
        }
        logging.debug(f'Сохранение данных в Supabase для {link}')
        supabase.table('producthunt').insert(data).execute()
        logging.info(f'Данные для {link} успешно сохранены в Supabase.')
