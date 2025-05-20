from bs4 import BeautifulSoup
import requests
import neologdn
import re
from urllib.parse import urljoin

debug = True

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

    article_title = ''
    content = []

    time_tag = section_to_use.find('time')
    article_datetime = time_tag.get('datetime') if time_tag and time_tag.has_attr('datetime') else None

    for tag in section_to_use.find_all(True):  # All tags
        # Only capture direct text (not from children)
        tag_text = ''.join(tag.find_all(string=True, recursive=False)).strip()
        normalized_text = neologdn.normalize(tag_text)

        # if the tag has text and was normalized, get it's class and parent class and store them as strings
        if normalized_text:
            class_ = ' '.join(tag.get('class')) if tag.has_attr('class') else None

            if (parent := tag.find_parent(attrs={'class': True})):
                parent_class = ' '.join(parent.get('class', []))
            else:
                parent_class = None
            # if the text has a title tag, store that as the title for all sections
            if parent_class == 'content--title' or class_ == 'contentTitle':
                article_title = normalized_text

            content.append({
                'article_title': article_title,
                'date': article_datetime,
                'text': normalized_text,
                'tag': tag.name,
                'class': class_,
                'parent_class': parent_class,
                'url': url
            })
            if debug == True:
                print(f"Article_title: {article_title}\nDate: {article_datetime}\n"
                      f"Text: {normalized_text}\nTag: <{tag.name}>\n"
                      f"Class: {class_}\nParent class: {parent_class}\n---")
    return content

homepage = 'https://www3.nhk.or.jp/news/'
articles = get_articles(homepage)

# pull the text from all articles
for article in articles:
    print(article[1])
    text = extract_text(article[1])
    #print(text)

#extract only the kanji
if False:
    for article in articles:
        text = article.text
        kanji = re.findall(r'[\u4e00-\u9faf]+', text)
        print(text)
        print(kanji)
