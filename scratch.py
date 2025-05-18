from bs4 import BeautifulSoup
import requests
import neologdn
import re
from urllib.parse import urljoin

#site map for news articles of the last 3 days
#probably a smarter way to pull the links
#https://www3.nhk.or.jp/news/sitemap-news-flow-3days.xml

# a function which takes a URL and returns the parsed text in an object
def get_response(url):
    response = requests.get(url)
    response.encoding = 'utf-8'  # force utf-8 for Japanese text
    return BeautifulSoup(response.text, 'html.parser')

def get_articles(homepage):
    soup = get_response(homepage)
    articles = []

    for a in soup.find_all('a'):
        title_tag = a.find('em', class_='title')
        if title_tag:
            tag_text = title_tag.get_text(strip=True)
            normalized_text = neologdn.normalize(tag_text)
            href = a.get('href')
            full_url = urljoin(homepage, href)
            articles.append([normalized_text, full_url])
    return articles

def extract_text(url):
    soup = get_response(url)

    # Try to scrape the page first
    main_section = soup.find('section', class_='module--detail-content')
    if main_section:
        section_to_use = main_section
    else:
        # Fallback to no-JS version
        nojs_section = soup.find('section', class_='detail-no-js')
        if nojs_section:
            section_to_use = nojs_section
        else:
            print("No recognizable content section found.")
            return []

    content = []

    for tag in section_to_use.find_all(True):  # All tags
        # Only capture direct text (not from children)
        tag_text = ''.join(tag.find_all(string=True, recursive=False)).strip()
        normalized_text = neologdn.normalize(tag_text)

        if normalized_text:
            parent_with_class = tag.find_parent(attrs={'class': True})
            class_name = ' '.join(parent_with_class.get('class')) if parent_with_class else None
            content.append({
                'text': normalized_text,
                'tag': tag.name,
                'class': ' '.join(tag.get('class')) if tag.has_attr('class') else None,
                'parent_class': class_name
            })
            # print(f"Text: {text}\nTag: <{tag.name}>\nClass: {tag.get('class')}\nParent class: {class_name}\n---")
    return content

homepage = 'https://www3.nhk.or.jp/news/'
articles = get_articles(homepage)

for article in articles:
    print(article[1])
    text = extract_text(article[1])
    print(text)


#extract only the kanji
if False:
    for article in articles:
        text = article.text
        kanji = re.findall(r'[\u4e00-\u9faf]+', text)
        print(text)
        print(kanji)
