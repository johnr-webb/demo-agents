import logging
from dotenv import load_dotenv
from agent import chat
from tools import FOLDER

logging.getLogger("LiteLLM").setLevel(logging.ERROR)

if __name__ == "__main__":
    load_dotenv()
    print(f"Working folder: {FOLDER}\nType 'exit to quit")
    chat()