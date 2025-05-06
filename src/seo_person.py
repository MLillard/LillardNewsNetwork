import json
import re
from collections import Counter
from typing import Dict, List, Tuple


class SEOAnalyzer:
    def __init__(self):
        # Writing style and tone guidelines
        self.writing_style = {
            'voice': """
                Write with the authority of an Ivy League-educated field journalist. 
                Blend the commanding presence of Anderson Cooper, the engaging style of Don Lemon, 
                and the investigative depth of a Philadelphia print journalist. 
                Your words should command attention, convey impact, and drive engagement without unnecessary fluff.
            """,
            'structure': """
                - Lead with a powerful, hook-driven first paragraph that captures attention within 30 words
                - Maintain journalistic integrity while optimizing for search visibility
                - Create quotable, shareable sections that resonate on social media
                - Format for digital readability with well-structured paragraphs
                - Ensure content feels authentically human, avoiding AI detection patterns
                - Write title without 'Title:' prefix
                - Lead with a unique first paragraph that doesn't repeat the title
            """,
            'tone': """
                Balance professional authority with accessible insight.
                Not academic, not casual - aim for the sweet spot that engages both
                professionals and general readers while maintaining credibility.
            """,
        }

        # Regional keywords for local SEO
        self.local_terms = {
            'primary': ['Delaware', 'Philadelphia', 'Wilmington', 'Newark', 'Dover'],
            'regions': ['Mid-Atlantic', 'Pennsylvania', 'New Jersey', 'Maryland'],
            'local': ['Main Street', 'Market Street', 'Delaware Valley', 'First State'],
        }

        # Words to avoid in SEO
        self.generic_terms = {
            'news',
            'update',
            'report',
            'latest',
            'breaking',
            'today',
            'announces',
            'announced',
            'says',
            'stated',
            'reported',
        }

    def analyze_content(self, content: str, title: str) -> Dict:
        """Analyze content for SEO optimization"""
        # Extract meaningful keywords
        keywords = self._extract_keywords(content, title)

        # Generate meta content
        meta = self._generate_meta(title, content, keywords)

        # Determine category and tags
        category, tags = self._determine_tags(content, keywords)

        return {
            'primary_keyword': keywords['primary'],
            'supporting_keywords': keywords['secondary'],
            'meta_title': meta['title'],
            'meta_description': meta['description'],
            'category': category,
            'tags': tags,
            'writing_guidelines': self.writing_style,
        }

    def _extract_keywords(self, content: str, title: str) -> Dict[str, List[str]]:
        """Extract high-impact keywords"""
        # Clean and tokenize content
        words = re.findall(r'\b\w+\b', f"{title} {content}".lower())
        word_freq = Counter(words)

        # Remove generic terms
        for term in self.generic_terms:
            word_freq.pop(term, None)

        # Find local relevance
        local_relevance = [word for word in words if word in [x.lower() for x in sum(self.local_terms.values(), [])]]

        # Get most significant terms
        significant_terms = [
            word for word, _ in word_freq.most_common(10) if len(word) > 3 and word not in self.generic_terms
        ]

        # Determine primary keyword (prioritize local terms if relevant)
        primary = (local_relevance[0] if local_relevance else significant_terms[0]).title()

        # Supporting keywords (excluding primary)
        secondary = [word.title() for word in significant_terms[1:6] if word.title() != primary]

        return {'primary': primary, 'secondary': secondary}

    def _generate_meta(self, title: str, content: str, keywords: Dict) -> Dict[str, str]:
        """Generate optimized meta content"""
        # Create SEO title (max 59 chars)
        meta_title = f"{title[:57]}..." if len(title) > 60 else title

        # Create meta description (max 144 chars)
        first_para = content.split('\n')[0]
        meta_desc = f"{first_para[:142]}..." if len(first_para) > 145 else first_para

        return {'title': meta_title, 'description': meta_desc}

    def _determine_tags(self, content: str, keywords: Dict) -> Tuple[str, List[str]]:
        """Determine category and tags"""
        # Use keywords to suggest relevant tags
        tags = [keywords['primary']] + keywords['secondary'][:3]

        # Add local tag if relevant
        if any(term.lower() in content.lower() for term in self.local_terms['primary']):
            tags.append('Delaware News')

        return 'News', tags  # Category will be refined by the publisher


def analyze_article(article_path: str) -> Dict:
    """Analyze article and return SEO recommendations"""
    with open(article_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    analyzer = SEOAnalyzer()
    seo_data = analyzer.analyze_content(data['content'], data['title'])
    return seo_data
