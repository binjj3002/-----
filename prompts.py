# Template for vocabulary analysis
PROMPT_VOCABULARY = """
Analyze the following Korean text and extract key vocabulary. For each word:
1. Provide the word in Korean
2. Give its meaning in English
3. Add usage notes and context
4. Include common collocations if applicable

Format the response as follows:
Word: [Korean word]
Meaning: [English meaning]
Usage: [Usage notes and context]

Input text:
{text}
"""

# Template for grammar analysis
PROMPT_GRAMMAR = """
Analyze the following Korean text and identify grammar patterns. For each pattern:
1. Show the grammar structure
2. Explain its usage and meaning
3. Provide an example from the text or a similar example

Format the response as follows:
Pattern: [Grammar pattern]
Explanation: [Usage and meaning]
Example: [Example sentence]

Input text:
{text}
"""

# Template for URL content analysis
PROMPT_URL = """
Analyze the Korean text content from this URL. Extract both vocabulary and grammar patterns.
Follow the same format as the text analysis.

URL content:
{text}
"""