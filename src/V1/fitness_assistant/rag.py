import json
import requests
from time import time
import ingest

OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Ollama API endpoint
index = ingest.load_index()


def search(query):
    boost = {
        'name': 2.5,               # Exercise name gets high priority
        'category': 1.8,           # Type of exercise category
        'equipment': 1.2,          # Equipment needed
        'force': 1.0,              # Type of force (push/pull etc.)
        'instructions': 0.7,       # Detailed instructions (lower priority as it's lengthy)
        'level': 1.5,              # Difficulty level
        'mechanic': 1.3,           # Exercise mechanics
        'primaryMuscles': 2.2,     # Primary muscles targeted (high priority)
        'secondaryMuscles': 1.6    # Secondary muscles worked
    }

    results = index.search(
        query=query, filter_dict={}, boost_dict=boost, num_results=10
    )

    return results


prompt_template = """
You're a fitness instructor. Answer the QUESTION based on the CONTEXT from our exercises database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT:
{context}
""".strip()


entry_template = """
"name": {name},
"category": {category},
"equipment": {equipment},
"force": {force},
"instructions": {instructions},
"level": {level},
"mechanic": {mechanic},
"primaryMuscles": {primaryMuscles},
"secondaryMuscles": {secondaryMuscles}
""".strip()


def build_prompt(query, search_results):
    context = ""

    for doc in search_results:
        context = context + entry_template.format(**doc) + "\n\n"

    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt


def llm(prompt, model="llama3.2:latest"):
    # Send request to Ollama's API
    payload = {
        "model": model,
        "prompt": prompt
    }
    response = requests.post(OLLAMA_API_URL, json=payload)

    if response.status_code == 200:
        json_response = response.json()
        answer = json_response.get("content", "")
        return answer, None  # Ollama does not provide token statistics
    else:
        raise Exception(f"Ollama API error: {response.status_code} - {response.text}")


evaluation_prompt_template = """
You are an expert evaluator for a RAG system.
Your task is to analyze the relevance of the generated answer to the given question.
Based on the relevance of the generated answer, you will classify it
as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Here is the data for evaluation:

Question: {question}
Generated Answer: {answer}

Please analyze the content and context of the generated answer in relation to the question
and provide your evaluation in parsable JSON without using code blocks:

{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Provide a brief explanation for your evaluation]"
}}
""".strip()


def evaluate_relevance(question, answer):
    prompt = evaluation_prompt_template.format(question=question, answer=answer)
    evaluation, _ = llm(prompt, model="gpt-4o-mini")

    try:
        json_eval = json.loads(evaluation)
        return json_eval
    except json.JSONDecodeError:
        result = {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
        return result


def calculate_openai_cost(tokens):
    # Ollama does not charge per token in the same way OpenAI does, so this can be omitted or customized.
    return 0


def rag(query, model="gpt-4o-mini"):
    t0 = time()

    search_results = search(query)
    prompt = build_prompt(query, search_results)
    answer, _ = llm(prompt, model=model)

    relevance = evaluate_relevance(query, answer)

    t1 = time()
    took = t1 - t0

    answer_data = {
        "answer": answer,
        "model_used": model,
        "response_time": took,
        "relevance": relevance.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance.get(
            "Explanation", "Failed to parse evaluation"
        ),
    }

    return answer_data
