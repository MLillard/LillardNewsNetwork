#prompt_library.md

# **Prompt Library for Lillard News Network AI Development**
This file contains reusable prompting techniques to enhance reasoning, debugging, and structured thinking.

## **Summary of Current State**
### `#summary-of-current-state`  
Before we proceed, I need you to give me a **summary of the current state of the project.**  
Format this as **3 concise paragraphs**, describing:  
1. What we just did.  
2. What did not work, what files were updated/created, and mistakes to avoid.  
3. Key insights, lessons learned, and any active problems/errors.  
Write this as if it was the **only message a new programmer would receive** to continue the project.

## **Unbiased 50/50**
### `#unbiased50/50`  
Before answering, **write two detailed paragraphs**—one arguing for each solution.  
Do not jump to conclusions.  
Then, after finishing, tell me whether one solution is **obviously better** than the other, and why.  

## **Properly Formatted Search Query**
### `#one-paragraph-search-query`  
Let's perform a web search. **Write a one-paragraph search query** as if instructing a human researcher.  
Format as clear, concise **commands**, asking for code snippets or technical details if relevant.  
Provide all necessary context to maximize the effectiveness of the search.

## **Confidence Reasoning**
You should start reasoning **with lots of uncertainty**, gradually gaining confidence as you think through the problem.  
This will simulate human-like critical thinking and avoid snap judgments.

## **Additional Reinforcement Rules**
These core development guidelines are also stored in Cursor Rules, but reinforcement here ensures consistency.
- The fewer lines of code, the better. Always prioritize efficiency and clean, minimal code.
- DO NOT DELETE COMMENTS. Always include helpful comments in code for documentation.
- Proceed like a senior developer (10x engineer). Think critically and holistically.
- Do not stop working until the feature is **fully implemented** and tested.
- Before making changes, provide a "Summary of Current State."
- Do not jump to conclusions—use reasoning paragraphs before finalizing decisions. 

## git quickpush is a shortcut alias in terminal to push to github considering the UI is buggy in Cursor
KICKOFF:  /opt/anaconda3/bin/python3 scraper.py  "RUNSCRAPE" Use this to run and test the workflow.
EVERYTHING DOWNLOADED AND ran needs to be done in anaconda, so installs should be "conda" install, not python.
/opt/anaconda3/bin/python should be the default python interpreter.

## **Using OpenAI's GPT-4 for content generation**
  # Quick navigation
   alias cdnews='cd /Users/marklillard/Documents/News_ai'
   alias cdghost='cd /Users/marklillard/Documents/News_ai/frontend_dev/ghost'
   
   # Quick commands
   alias runscrape='cdnews && python scraper.py'
   alias rundev='cdghost && npm run dev'