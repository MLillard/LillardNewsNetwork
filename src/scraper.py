import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from publish_to_ghost import GhostPublisher
from seo_post_publish import SEOPostPublisher


class NewsArticleScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.output_dir = Path('articles')
        self.output_dir.mkdir(exist_ok=True)

    def scrape_article(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            article_data = {'title': self._get_title(soup), 'content': self._get_content(soup), 'url': url}

            print(f"Successfully scraped article: {article_data['title']}")
            return article_data

        except Exception as e:
            print(f"Error scraping article: {str(e)}")
            return None

    def _get_title(self, soup):
        title = soup.find('h1')
        return title.text.strip() if title else ''

    def _get_content(self, soup):
        for unwanted in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            unwanted.decompose()

        content = soup.find('article') or soup.find(class_=['article-body', 'content'])

        if content:
            paragraphs = content.find_all('p')
            return '\n\n'.join(p.text.strip() for p in paragraphs if p.text.strip())
        return ''

    def save_article(self, article_data):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.output_dir / f'article_{timestamp}.json'

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            print(f"Article saved to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving article: {str(e)}")
            return None

    def process_with_news_writer(self, article_file):
        try:
            news_writer_path = Path('news_writer.py')

            process = subprocess.run(
                [sys.executable, str(news_writer_path), str(article_file)], capture_output=True, text=True, check=True
            )

            # Get the generated file path
            generated_file = str(article_file).replace('.json', '_generated.txt')

            # Compare word counts
            with open(article_file, 'r', encoding='utf-8') as f:
                original = json.load(f)
                original_words = len(original['content'].split())

            with open(generated_file, 'r', encoding='utf-8') as f:
                generated = f.read()
                generated_words = len(generated.split())

            print("\nWORD COUNT COMPARISON:")
            print(f"Original article:  {original_words} words")
            print(f"Generated article: {generated_words} words")
            print(f"Difference:        {generated_words - original_words} words")

            # Show metadata preview first
            print("\nMETADATA PREVIEW:")
            seo = SEOPostPublisher()
            with open(generated_file, 'r', encoding='utf-8') as f:
                generated = f.read()
                title = generated.split('\n')[0]  # First line is title
            metadata = seo.analyze_content(generated, title)
            print(f"Title: {metadata['meta_title']}")
            print(f"Description: {metadata['meta_description']}")
            print(f"Keywords: {', '.join(metadata['keywords'])}\n")

            # Then publish to Ghost
            try:
                publisher = GhostPublisher()
                post_id = publisher.publish_article(generated_file)
                if post_id:
                    print("Article successfully published to Ghost")
                else:
                    print("Failed to publish to Ghost")
            except Exception as e:
                print(f"Error publishing to Ghost: {str(e)}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"Error running news_writer.py: {e.stderr}")
            return False
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return False


def main():
    scraper = NewsArticleScraper()
    url = "https://www.cbssports.com/nfl/news/2025-super-bowl-betting-10-best-super-bowl-59-picks-props-to-place-in-your-chiefs-vs-eagles-parlays/"

    article_data = scraper.scrape_article(url)

    if article_data:
        article_file = scraper.save_article(article_data)

        if article_file:
            if scraper.process_with_news_writer(article_file):
                print("Article processing completed successfully")
            else:
                print("Failed to process article")
        else:
            print("Failed to save scraped article")
    else:
        print("Failed to scrape article")


if __name__ == "__main__":
    main()
