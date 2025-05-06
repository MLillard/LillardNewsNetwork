import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from jwt import encode as jwt_encode

# Set up logging
logging.basicConfig(filename='../category_classification.log', level=logging.INFO, format='%(asctime)s - %(message)s')


class GhostPublisher:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.ghost_url = os.getenv('GHOST_API_URL')
        self.admin_key = os.getenv('GHOST_ADMIN_API_KEY')

        # Split the admin key into ID and Secret
        key_parts = self.admin_key.split(':')
        if len(key_parts) != 2:
            raise ValueError("Invalid Admin API key format")

        self.key_id = key_parts[0]
        self.key_secret = key_parts[1]

        if not all([self.ghost_url, self.admin_key]):
            raise ValueError("Missing Ghost API credentials in .env file")

        # API endpoint for posts
        self.api_url = f"{self.ghost_url}/ghost/api/admin/posts"

        # Enhanced category definitions with weighted keywords
        self.categories = {
            'Arts & Entertainment': {
                'primary': ['entertainment', 'movie', 'film', 'music', 'concert', 'actor', 'actress', 'celebrity'],
                'secondary': ['performance', 'award', 'director', 'artist', 'song', 'album', 'theater', 'show'],
            },
            'Finance': {
                'primary': ['finance', 'market', 'economy', 'stock', 'investment', 'business', 'trade'],
                'secondary': ['dollar', 'profit', 'revenue', 'growth', 'company', 'industry', 'price'],
            },
            'Food': {
                'primary': ['food', 'restaurant', 'chef', 'cuisine', 'dining'],
                'secondary': ['recipe', 'meal', 'menu', 'cooking', 'dish', 'taste', 'flavor'],
            },
            'Lifestyle': {
                'primary': ['lifestyle', 'fashion', 'health', 'wellness', 'fitness'],
                'secondary': ['trend', 'style', 'design', 'beauty', 'travel', 'living'],
            },
            'Politics': {
                'primary': ['politics', 'government', 'president', 'congress', 'election', 'biden', 'trump'],
                'secondary': ['policy', 'senator', 'democrat', 'republican', 'vote', 'campaign'],
            },
            'Sports': {
                'primary': ['sports', 'game', 'team', 'player', 'championship'],
                'secondary': ['win', 'score', 'season', 'league', 'coach', 'match', 'tournament'],
            },
        }

    def generate_token(self):
        """Generate JWT token for Ghost Admin API"""
        iat = int(datetime.now().timestamp())

        header = {'alg': 'HS256', 'kid': self.key_id, 'typ': 'JWT'}

        payload = {'iat': iat, 'exp': iat + 5 * 60, 'aud': '/v5/admin/'}

        return jwt_encode(payload, bytes.fromhex(self.key_secret), algorithm='HS256', headers=header)

    def read_article(self, file_path):
        """Read and parse article file"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Article file not found: {file_path}")

        if file_path.suffix == '.json':
            # Handle JSON files from scraper
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {'title': data['title'].strip()[:255], 'content': data['content']}  # Limit title length
        else:
            # Handle generated text files
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract first line as title, limit length
                lines = content.split('\n')
                title = lines[0].strip()[:255]  # Limit title length
                body = '\n'.join(lines[1:]).strip()
                return {'title': title, 'content': body}

    def publish_article(self, article_path):
        """Publish article to Ghost"""
        try:
            article = self.read_article(article_path)

            # Get SEO metadata
            from seo_post_publish import SEOPostPublisher

            seo = SEOPostPublisher()
            # Use the AI-generated content for metadata, not the original
            generated_file = article_path.replace('.json', '_generated.txt')
            with open(generated_file, 'r', encoding='utf-8') as f:
                generated_content = f.read()
            formatted_content = self.format_content_html(generated_content)
            metadata = seo.analyze_content(generated_content, article['title'])

            post_data = {
                'posts': [
                    {
                        'title': article['title'],
                        'mobiledoc': json.dumps(
                            {
                                "version": "0.3.1",
                                "markups": [],
                                "atoms": [],
                                "cards": [["html", {"html": formatted_content}]],
                                "sections": [[10, 0]],
                            }
                        ),
                        'status': 'published',
                        'tags': [{'name': self.determine_category(article['content'])}],
                        'authors': ['AI News Writer'],
                        'meta_title': metadata['meta_title'],
                        'meta_description': metadata['meta_description'],
                        'custom_excerpt': metadata['excerpt'],
                    }
                ]
            }

            # Make the API request
            token = self.generate_token()
            headers = {'Authorization': f'Ghost {token}', 'Content-Type': 'application/json'}

            response = requests.post(self.api_url, json=post_data, headers=headers)

            if response.status_code == 201:  # Created successfully
                post = response.json()['posts'][0]
                print(f"\nPublished: {article['title']}")
                print(f"URL: {self.ghost_url}/{post['slug']}")
                return post['id']  # Return the post ID
            else:
                print(f"\nFailed to publish. Status code: {response.status_code}")
                print(f"Error: {response.text}")
                return None

        except Exception as e:
            print(f"\nError publishing article: {str(e)}")
            return None

    def format_content_html(self, content):
        """Format content as HTML with proper styling"""
        paragraphs = content.split('\n\n')
        formatted_paragraphs = [f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()]
        return '\n'.join(formatted_paragraphs)

    def determine_category(self, content):
        """Determine article category based on content analysis"""
        content = content.lower()
        scores = {category: 0 for category in self.categories}

        for category, keywords in self.categories.items():
            # Check primary keywords (higher weight)
            for word in keywords['primary']:
                if word.lower() in content:
                    scores[category] += 2

            # Check secondary keywords (lower weight)
            for word in keywords['secondary']:
                if word.lower() in content:
                    scores[category] += 1

        # Log the categorization process
        logging.info(f"Category scores: {scores}")

        # Get category with highest score
        max_score = max(scores.values())
        if max_score > 0:
            category = max(scores, key=scores.get)
            logging.info(f"Selected category: {category}")
            return category

        # Default category if no strong matches
        logging.info("No strong category match, defaulting to 'News'")
        return 'News'


def main():
    if len(sys.argv) < 2:
        print("Usage: python publish_to_ghost.py <article_file>")
        sys.exit(1)

    article_path = sys.argv[1]

    try:
        publisher = GhostPublisher()
        post_id = publisher.publish_article(article_path)

        if post_id:
            print("\nArticle published successfully")
            print(f"Post ID: {post_id}")
        else:
            print("\nFailed to publish article")
            sys.exit(1)

    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
