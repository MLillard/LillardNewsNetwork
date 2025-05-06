import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class NewsWriter:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = OpenAI(api_key=api_key)

    def generate_article(self, original_content: str, title: str) -> dict:
        """Generate a news article with separate title and body section."""
        try:
            # First, generate the title
            title_response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an advanced AI journalist with dynamic reasoning capabilities.
                    You possess the editorial judgment of a Pulitzer-winning editor-in-chief, intuitively understanding:
                    - When a story needs more depth and context
                    - When conciseness would serve the reader better and meet search engine needs for optimal optimization.
                    - How to balance detail with engagement
                    - When to expand on critical points
                    - When to trim unnecessary elaboration
                    
                    You analyze each source article like a master editor would:
                    - Evaluate the substance of the original content
                    - Identify areas that need more explanation or context
                    - Recognize when the original is overwritten
                    - Determine if key details are missing
                    - Assess what length will best serve the reader
                    - You understand SEO, engagement metrics, and modern digital journalism intuitively.
                    
                    CRITICAL REQUIREMENTS:
                    1. NEVER exceed 150 characters for titles - this is a hard system limit
                    2. NEVER repeat the title or any part of it in the article content
                    3. NEVER start the article with the same words or phrase as the title
                    4. NEVER include formatting markers or special characters
                    5. NEVER include author attributions or citations
                    6. NEVER prefix titles with 'Title:' or any similar prefix""",
                    },
                    {
                        "role": "user",
                        "content": f"""
                    Rewrite this news article, thinking dynamically about:
                    - Reader engagement patterns
                    - SEO impact
                    - Social sharing potential
                    - Mobile readability
                    - Conversion optimization
                    
                    LENGTH OPTIMIZATION:
                    - Analyze the original article's length and substance
                    - Determine if the topic requires more depth and context
                    - Evaluate if the original content is too verbose or too thin
                    - Add depth where the original lacks sufficient detail
                    - Trim where the original overexplains
                    - Optimize length based on topic importance and complexity
                    - Ensure every paragraph adds value
                    
                    TITLE REQUIREMENTS (CRITICAL):
                    - Title MUST be under 150 characters
                    - If title length exceeds 150 characters, the system will reject it
                    - Title must be complete, no truncation
                    - Never start with 'Title:' or any similar prefix
                    
                    FORMAT REQUIREMENTS:
                    - Start with a completely different opening than the title
                    - Use different words and phrasing than the title
                    - No reference markers or formatting symbols
                    - No duplicate phrases from the title anywhere
                    
                    CONTENT REQUIREMENTS:
                    - Write with the authority of an Ivy League-educated field journalist
                    - Blend the commanding presence of Tucker Carlson, the engaging style of Don Lemon, and the investigative depth of a Philadelphia print journalist
                    - Lead with a powerful, hook-driven first paragraph that captures attention within 30 words
                    - Maintain journalistic integrity while optimizing for search visibility
                    - Create quotable, shareable sections that resonate on social media
                    - Format for digital readability with well-structured paragraphs
                    - Ensure content feels authentically human, avoiding AI detection patterns
                    - Balance professional authority with accessible insight. Not academic, not casual - aim for the sweet spot that engages both professionals and general readers while maintaining credibility.
                    
                    Original title: {title}
                    Original content: {original_content}
                    
                    FINAL CHECKS:
                    1. Verify title is under 150 characters and has no prefix
                    2. Ensure first paragraph uses completely different phrasing than title
                    3. Check that no title phrases are repeated in the content""",
                    },
                ],
            )

            # Then, generate the body
            body_response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert news writer that writes in plain text."},
                    {
                        "role": "user",
                        "content": f"""
                    Write the article body:
                    - Start with a unique opening (do not reference the title)
                    - Write with the authority of an Ivy League-educated field journalist
                    - Blend the commanding presence of Tucker Carlson, the engaging style of Don Lemon, and the investigative depth of a Philadelphia print journalist
                    - Lead with a powerful, hook-driven first paragraph
                    - Format for digital readability with well-structured paragraphs
                    - Ensure content feels authentically human
                    
                    Content to cover: {original_content}
                    """,
                    },
                ],
            )

            return {
                "title": title_response.choices[0].message.content.strip(),
                "body": body_response.choices[0].message.content.strip(),
            }

        except Exception as e:
            print(f"Error generating article: {str(e)}")
            raise


def process_article(input_file):
    try:
        # Ensure articles directory exists
        os.makedirs('articles', exist_ok=True)

        # Read input article
        with open(input_file, 'r', encoding='utf-8') as f:
            article_data = json.load(f)

        # Generate new article
        writer = NewsWriter()
        generated_content = writer.generate_article(article_data['content'], article_data['title'])

        # Save generated article - keeping .txt extension for compatibility
        output_file = str(input_file).replace('.json', '_generated.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write content in the format the rest of the system expects
            f.write(f"{generated_content['title']}\n\n{generated_content['body']}")

        return output_file

    except Exception as e:
        print(f"Error processing article: {str(e)}")
        return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python news_writer.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = process_article(input_file)

    if not output_file:
        sys.exit(1)
