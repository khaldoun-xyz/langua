# chat.py
import argparse
import os
from datetime import datetime

import psycopg2
from dotenv import load_dotenv
from groq import Groq
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("MODEL")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PW = os.getenv("POSTGRES_PW")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

client = Groq(api_key=GROQ_API_KEY)

def create_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PW,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def log_conversation_to_db(username, prompt, response, start_time, end_time, interaction_count):
    conn = create_db_connection()
    if conn is None:
        print("Could not connect to database.")
        return
    try:
        if start_time is None or end_time is None:
            print(f"Start time or end time is None for user: {username}. Cannot log conversation.")
            return
        
        duration = end_time - start_time
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO conversations (username, prompt, response, created_at, start_time, end_time, interaction_count, duration)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (username, prompt, response, datetime.now(), start_time, end_time, interaction_count, duration)
            )
            conn.commit()
    except Exception as e:
        print(f"Error logging conversation: {e}")
    finally:
        conn.close()

def get_groq_response(conversation_history):
    try:
        response = groq_llm_api_call(conversation_history)
        return response.strip()
    except Exception as e:
        return f"Error: {e}"

def groq_llm_api_call(conversation_history):
    chat_completion = client.chat.completions.create(
        messages=conversation_history,
        model=MODEL,
    )
    return chat_completion.choices[0].message.content

def chat_with_groq_llm(username):
    session = PromptSession(history=InMemoryHistory())
    style = Style.from_dict(
        {
            "prompt": "ansicyan bold",
            "response": "ansigreen",
        }
    )

    conversation_history = [
        {
            "role": "system",
            "content": "You reply in the language the user sends you.",
        }
    ]
    
    interaction_count = 0
    logging_enabled = False
    start_time = None
    end_time = None

    print("Welcome to Groq LLM Chat! Type 'exit' to quit, 'start evaluation' to begin logging, or 'stop evaluation' to stop logging.\n")
    while True:
        try:
            prompt = session.prompt("You: ")
            if prompt.lower() == "exit":
                if logging_enabled:
                    end_time = datetime.now()
                    log_conversation_to_db(username, "Conversation ended.", "Goodbye!", start_time, end_time, interaction_count)
                print("Exiting Groq LLM Chat. Goodbye!")
                break
            elif prompt.lower() == "start evaluation":
                logging_enabled = True
                start_time = datetime.now()
                print("Evaluation logging started.")
                continue
            elif prompt.lower() == "stop evaluation":
                if logging_enabled:  
                    end_time = datetime.now()  
                    logging_enabled = False  
                    print("Evaluation logging stopped.")  
                continue  

            conversation_history.append({"role": "user", "content": prompt})  
            response = get_groq_response(conversation_history)  
            print(f"\033[92mGroq LLM: {response}\033[0m\n")  

            interaction_count += 1  

            if logging_enabled:  
                end_time = datetime.now()  # Update end_time for each interaction during logging  
                log_conversation_to_db(username, prompt, response, start_time, end_time, interaction_count)  

            conversation_history.append({"role": "assistant", "content": response})  

        except (EOFError, KeyboardInterrupt):  
            if logging_enabled:  
                end_time = datetime.now()  
                log_conversation_to_db(username, "Session interrupted.", "Goodbye!", start_time, end_time, interaction_count)  
            print("\nExiting Groq LLM Chat. Goodbye!")  
            break  

if __name__ == "__main__":  
    parser = argparse.ArgumentParser(description="Chat with Groq LLM and log conversations.")  
    parser.add_argument("-u", "--user", required=True, help="Specify the username for logging")  
    args = parser.parse_args()  
    chat_with_groq_llm(args.user)  