import logging
import os
import re
from collections import Counter
from typing import Dict, List

import spacy
from dotenv import load_dotenv
from openai import OpenAI
from spacy.lang.en.stop_words import STOP_WORDS

load_dotenv()  # Load environment variables from .env

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class SEOPostPublisher:
    def __init__(self):
        # Initialize NLP model and AI model once
        self.nlp = spacy.load("en_core_web_sm")
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.common_words = STOP_WORDS

    def analyze_content(self, content: str, title: str) -> Dict:
        """Analyze the entire article content and extract metadata optimized for:
        - SEO (ensure high keyword density, proper structuring for search engines)
        - Engagement (make it compelling and click-worthy for readers)
        - Social Media Sharing (titles/descriptions that perform well on platforms like Twitter, Facebook)
        - Readability (clear, natural-sounding language, avoiding keyword stuffing)
        - Competitive Advantage (ensure metadata is stronger than similar articles in Google results)"""

        # Remove all author references and bylines
        content = re.sub(r'(?i)by\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', '', content)  # Matches "By John Smith"
        content = re.sub(
            r'(?i)[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\s+(?:reports|writes|reporting)', '', content
        )  # Matches "John Smith reports"
        content = re.sub(
            r'(?i)(?:reporter|author|journalist)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', '', content
        )  # Matches "Reporter John Smith"
        content = re.sub(r'(?i)for\s+(?:USA TODAY|Associated Press|Reuters)', '', content)  # Matches "for USA TODAY"

        # Extract and clean content
        clean_content = self._clean_html(content)

        # Extract and process keywords
        keywords = self._extract_keywords(clean_content, title)

        return {
            'keywords': keywords,
            'meta_title': self._create_meta_title(title, keywords[:2]),
            'meta_description': self._create_meta_description(clean_content, keywords[:3]),
            'excerpt': self._create_excerpt(clean_content),
        }

    def _clean_html(self, content: str) -> str:
        """Clean and normalize HTML content"""
        return re.sub('<[^<]+?>', '', content).strip().replace("\n", " ").replace("\r", " ")

    def _extract_keywords(self, clean_content: str, title: str) -> List[str]:
        """Extract and process keywords from content"""
        # Get initial word frequency
        words = re.findall(r'\b\w+\b', f"{title} {clean_content}".lower())
        word_freq = Counter(words)

        # Filter out common words
        word_freq = {word: freq for word, freq in word_freq.items() if word.lower() not in self.common_words}

        # Process with NLP for entities and phrases
        doc = self.nlp(clean_content)

        # Extract named entities and noun chunks
        entities = [ent.text for ent in doc.ents if len(ent.text) > 3]
        noun_chunks = [chunk.text for chunk in doc.noun_chunks if len(chunk.text) > 3]

        # Combine and deduplicate
        return list(set(entities + noun_chunks))[:10]

    def _create_meta_title(self, title: str, keywords: List[str]) -> str:
        """Generate an SEO-optimized meta title that:
        - Keeps the original article's intent intact.
        - Dynamically integrates high-value keywords.
        - Ensures readability and avoids abrupt truncation.
        - Stays within the 59-character limit."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI that writes plain text titles with no formatting, no emphasis, no bold, no special styling - exactly like regular article text.",
                    },
                    {
                        "role": "user",
                        "content": f"""
                    Create a title in plain text that:
                    - Must be written in regular text exactly like article paragraphs (no emphasis, no bold, no special formatting)
                    - Naturally incorporates these keywords: {', '.join(keywords)}
                    - Stays under 59 characters. This is a strict requirement.
                    - Is engaging and click-worthy
                    - Remember: The title must be under 59 characters on the first attempt.
                    
                    Original title: {title}
                    """,
                    },
                ],
            )
            meta_title = response.choices[0].message.content
            if len(meta_title) > 59:
                logging.warning("Meta title exceeded limit, requesting shorter version")
                return self._create_meta_title(title, keywords)  # Retry if too long
            return meta_title
        except Exception as e:
            logging.error(f"Failed to generate meta title: {str(e)}")
            raise

    def _create_meta_description(self, content: str, keywords: List[str]) -> str:
        """Create engaging meta description (max 144 chars)
        -Craft Concise Summaries: Develop brief yet informative summaries for each article, ensuring they accurately reflect the content and entice readers to click.
        -Incorporate relevant keywords naturally to enhance search engine visibility, understanding that while meta descriptions do not directly influence rankings, they can impact click-through rates.
        -Adhere to Character Limits: Ensure meta descriptions are within the optimal length to prevent truncation in search results.  The limit is 144 characters.
        -Maintain Uniqueness: Create distinct meta descriptions for each article to avoid duplication issues and provide clear distinctions between content pieces.
        -Align with Content: Ensure that each meta description accurately represents its corresponding article to maintain reader trust and reduce bounce rates.
        -Utilize Active Voice and Calls to Action: Engage readers by using active language and, where appropriate, include calls to action to encourage clicks.
        -Length: Aim for meta descriptions that are concise yet comprehensive. While there is some flexibility, keeping them within a certain character range ensures they display fully in search results.
        -Keyword Integration: Include primary keywords relevant to the article content to align with potential search queries.
        -Avoid Duplication: Ensure each meta description is unique to prevent confusion and potential SEO penalties.
        -Reflect Content Accurately: Misleading descriptions can lead to higher bounce rates; always ensure the meta description aligns with the article content.
        -Adaptability: Tailor meta descriptions to fit various article types, from news reports to opinion pieces, ensuring relevance and appeal.
        -Audience Awareness: Understand the target audience to craft descriptions that resonate and meet their expectations.
        -Performance Monitoring: Analyze metrics such as click-through rates to assess the effectiveness of meta descriptions and adjust strategies accordingly.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI that generates highly optimized, world-class SEO meta descriptions.",
                    },
                    {
                        "role": "user",
                        "content": f"""
                    Create a compelling meta description that:
                    - STRICT REQUIREMENT: Must be EXACTLY 144 characters or less (will be rejected if longer)
                    - Naturally incorporates key terms: {', '.join(keywords)}
                    - Uses a strong, contextually appropriate call-to-action
                    - Forms a complete thought (no ellipsis)
                    - Matches the content's tone and urgency
                    
                    Content: {content}
                    """,
                    },
                ],
            )
            meta_desc = response.choices[0].message.content
            if len(meta_desc) > 144:
                logging.warning("Meta description exceeded limit, requesting shorter version")
                return self._create_meta_description(content, keywords)  # Retry if too long
            return meta_desc
        except Exception as e:
            logging.error(f"Failed to generate meta description: {str(e)}")
            raise

    def _create_excerpt(self, content: str, retry_count=0) -> str:
        """Craft a high-impact article excerpt (249 char max) that drives engagement and conversions.

        - Hook Generation: Create an irresistible opening that captures attention and compels continued reading
        - Value Proposition: Clearly communicate the unique value and key insights readers will gain
        - Psychological Triggers: Incorporate proven psychological principles (curiosity gap, social proof, urgency)
        - SEO Enhancement: Optimize for both search engines and human readers with strategic keyword placement
        - Narrative Flow: Ensure the excerpt reads naturally while building intrigue and interest
        - Brand Voice: Maintain consistent tone and style that aligns with publication standards
        - Click Psychology: Use proven copywriting techniques that maximize click-through rates
        - Content Preview: Provide enough substance to demonstrate value without revealing all key points
        - Reader Journey: Guide the reader naturally from excerpt to full article with seamless transitions
        - Engagement Metrics: Structure excerpt to improve time-on-page and reduce bounce rates
        - Mobile Optimization: Ensure readability across all devices with appropriate length and formatting
        - A/B Testing Ready: Format allows for testing different hooks and psychological approaches
        - Analytics Integration: Support tracking of excerpt performance and reader behavior patterns"""

        MAX_RETRIES = 3
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI that creates compelling article excerpts. Always write complete sentences that end naturally. Your response MUST be under 249 characters or it will be rejected.",
                    },
                    {
                        "role": "user",
                        "content": f"""
                    Create a compelling excerpt that:
                    - Must be EXACTLY 249 characters or less. This is a strict requirement.
                    - Must end with a complete sentence (no truncation)
                    - Never include author names or bylines
                    - Opens with a powerful hook
                    - Creates urgency without ellipses
                    - Use concise language and avoid unnecessary details
                    - Remember: The excerpt must be under 249 characters.
                    
                    Content: {content}
                    """,
                    },
                ],
            )
            excerpt = response.choices[0].message.content
            if len(excerpt) > 249:
                if retry_count < MAX_RETRIES:
                    logging.warning("Excerpt exceeded limit, requesting shorter version")
                    return self._create_excerpt(content, retry_count + 1)
                else:
                    logging.warning("Max retries reached, returning truncated excerpt")
                    # Truncate to the last complete sentence within the limit
                    truncated_excerpt = excerpt[:249].rsplit('.', 1)[0] + '.'
                    return truncated_excerpt
            return excerpt
        except Exception as e:
            logging.error(f"Failed to generate excerpt: {str(e)}")
            raise
