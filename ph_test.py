import datetime
import requests
import os
from bs4 import BeautifulSoup

ph_auth = os.getenv("PH_API_KEY")

month = datetime.datetime.today().month - 1
year = datetime.datetime.today().year

def get_best_posts(month, year):
    # Создаем даты начала и конца месяца
    start_date = datetime.datetime(year, month, 1).isoformat()
    if month == 12:
        end_date = datetime.datetime(year + 1, 1, 1).isoformat()
    else:
        end_date = datetime.datetime(year, month + 1, 1).isoformat()

    url = f"https://api.producthunt.com/v2/api/graphql"
    headers = {
        "Authorization": f"Bearer {ph_auth}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    query = """
    {
      posts(order: VOTES, postedAfter: "%s", postedBefore: "%s", first: 50) {
        edges {
          node {
            id
            name
            tagline
            votesCount
            url
          }
        }
      }
    }
    """ % (start_date, end_date)
    
    response = requests.post(url, headers=headers, json={"query": query})
    if response.status_code == 200:
        data = response.json()
        if 'data' not in data:
            raise Exception(f"Неверный формат ответа API: {data}")
        if 'posts' not in data['data']:
            raise Exception(f"Отсутствует ключ 'posts' в ответе: {data}")
        if 'edges' not in data['data']['posts']:
            raise Exception(f"Отсутствует ключ 'edges' в ответе: {data}")
            
        posts = data['data']['posts']['edges']
        best_posts = []
        for post in posts:
            node = post['node']
            best_posts.append({
                'id': node['id'],
                'name': node['name'],
                'tagline': node['tagline'],
                'votes': node['votesCount'],
                'url': node['url']
            })
        return best_posts
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def get_page_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Удаляем ненужные элементы
        for script in soup.find_all('script'):
            script.decompose()
        for style in soup.find_all('style'):
            style.decompose()
        
        # Получаем основной контент
        content = soup.get_text(separator='\n', strip=True)
        return content
    except Exception as e:
        return f"Ошибка при получении контента: {str(e)}"

if __name__ == "__main__":
    try:
        best_posts = get_best_posts(month, year)
        
        # Получаем контент только для первых 5 постов
        for post in best_posts[:5]:
            print(f"\nНазвание: {post['name']}")
            print(f"Описание: {post['tagline']}")
            print(f"Голоса: {post['votes']}")
            print(f"Ссылка: {post['url']}")
            print("\nКонтент страницы:")
            content = get_page_content(post['url'])
            print("=" * 80)
            print(content[:1000] + "...") # Выводим первые 1000 символов
            print("=" * 80)
            print("\n")
    except Exception as e:
        print(f"Ошибка: {e}")

