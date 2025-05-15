from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urljoin


def get_response(url):
    response = requests.get(url)
    response.encoding = 'utf-8'  # force utf-8 for Japanese text
    return BeautifulSoup(response.text, 'html.parser')

def get_article(url):
    print(url)
    soup = get_response(url)

    h1 = soup.find('h1')
    title = h1.get_text(strip=True) if h1 else 'Title not found'

    # Extract the title from <span class="contentTitle">
    #title = soup.find('span', {'class': 'contentTitle'}).get_text(strip=True) if soup.find('span', {
    #    'class': 'contentTitle'}) else 'Title not found'

    # Extract the main article text from <div id="news_textbody">
    main_content = soup.find('div', {'id': 'news_textbody'})
    article_text = main_content.get_text(strip=True) if main_content else 'Article content not found'

    # Extract every <div class="news_add">
    news_adds = soup.find_all('div', {'class': 'news_add'})
    additional_content = '\n'.join(
        [div.get_text(strip=True) for div in news_adds]) if news_adds else 'No additional content found'

    # Print the results
    print(f"Title: {title}")
    print(f"Article Text: {article_text}")
    print(f"Additional Content: {additional_content}")


def extract_all_sections_text(url):
    # Use get_response() to fetch and parse the HTML
    soup = get_response(url)

    content = []

    # Find all <section> tags
    sections = soup.find_all('section')
    for section in sections:
        # Get all the text within each <section>, removing extra spaces
        text = section.get_text(separator='\n', strip=True)
        if text:
            content.append(text)

    # Return all the combined text
    return '\n\n'.join(content) if content else 'Article body not found'


url = 'https://www3.nhk.or.jp/news/'  # Replace with actual URL
soup = get_response(url)

# Find all article titles and links
if True:
    articles = soup.find_all('em', class_='title')
    links = [a['href'] for a in soup.find_all('a') if a.find('em', class_='title')]

    results = []
    for a in soup.find_all('a'):
        title_tag = a.find('em', class_='title')
        if title_tag:
            text = title_tag.get_text(strip=True)
            href = a.get('href')
            full_url = urljoin(url, href)
            results.append([text, full_url])

    for result in results:
        print(result)
     #######    start from here
     # try to pull p class="content--summary"
    #h2 class="body-title"
    # div class="body-text"
 #       print(extract_all_sections_text(result[1]))

    #extract only the kanji
    if False:
        for article in articles:
            text = article.text
            kanji = re.findall(r'[\u4e00-\u9faf]+', text)
            print(text)
            print(kanji)

if False:
    # URL of the news article
    url = "https://www3.nhk.or.jp/news/html/20250508/k10014799641000.html"
    url = 'https://www3.nhk.or.jp/news/html/20250509/k10014801161000.html'


