import openai
from mastodon import Mastodon
import logging
import time
import json
import sys
from datetime import datetime, timedelta
import os
import re

# Logging
logging.basicConfig(filename='weatherbot.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
# Create a handler for stdout (standard output)
stdout_handler = logging.StreamHandler(sys.stdout)
# Add the stdout handler to the root logger
logging.getLogger().addHandler(stdout_handler)

# Define time of day:
time_of_day = datetime.now().hour
if time_of_day < 10:
    time_of_day = "morning"
elif time_of_day < 18:
    time_of_day = "afternoon"
else:
    time_of_day = "evening"
logging.info(f"Time of day: {time_of_day}")

# Read config
try:
    with open('config.json') as f:
        config = json.load(f)

        mastodon_access_token = config['mastodon_access_token']
        mastodon_base_url = config['mastodon_base_url']

        openai_api_key = config['openai_api_key']
        openai_max_tokens = config['max_tokens']
        openai_temperature = config['temperature']

        post_interval = config['post_interval']
except Exception as e:
    logging.error(e)
    exit()

openai_prompt = f"""
Provide a weather forecast for a fantastical city, town, or place
with the following structure:

1: Introduction:
Introduce as Zorblerg, the meteorologist of a fantasy realm.
Mention the specific fantasy locale. 
The introduction should be set in the {time_of_day} and
carry a friendly and imaginative tone.

2: Forecast:
Offer the {time_of_day}'s weather forecast for the specified fantasy location.
The forecast should be imaginative and engage the reader's fantasy expectations.
Use emojis to make the description lively, but ensure the entire forecast remains under 1000 characters.
Avoid using hashtags in this section.

3: Farewell:
Conclude with a statement related to the provided forecast. Provide a fond farewell to the readers.
In this section, incorporate hashtags for social media engagement.

Use the following strict headings for each section:
1: Introduction
2: Forecast
3: Farewell
"""

# OpenAI setup
openai.api_key = openai_api_key
openai.prompt = openai_prompt
# openai.max_tokens = openai_max_tokens
openai.temperature = openai_temperature

# Mastodon API setup
m = Mastodon(access_token=mastodon_access_token,
             api_base_url=mastodon_base_url)

# Variables
post_count = 1


# Functions
# --- Clear screen ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# --- Print banner ---
def print_banner():
    banner = """
     _____           _     _                
    / _  / ___  _ __| |__ | | ___ _ __ __ _ 
    \// / / _ \| '__| '_ \| |/ _ \ '__/ _` |
     / //\ (_) | |  | |_) | |  __/ | | (_| |
    /____/\___/|_|  |_.__/|_|\___|_|  \__, |
                                      |___/
    Zorblerg's Weather Bot - Bringing Fantasy Weather to Life 🌦️🌈
    """
    print(banner)


def get_models():
    models = openai.Model.list()
    print(models)


# --- Get weather forecast from OpenAI ---
def openai_get_weather():
    completion = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=[{"role": "user",
                  "content": openai_prompt}],
        max_tokens=int(openai_max_tokens))
    forecast = completion.choices[0].message.content
    logging.info(forecast)
    logging.info(len(forecast))
    print(len(forecast))
    return forecast


# --- Split string into chunks ---
def chunk_string_with_counters(s, chunk_size=500):
    # Preprocess the string
    s = s.replace("1: Introduction\n", "-XX-").replace(
        "2: Forecast\n", "-XX-").replace("3: Farewell\n", "-XX-").replace("\n", "").strip()

    # Split the string into sections
    sections = s.split("-XX-")[1:]  # the first element is empty due to the leading "-XX-"

    # Check if we have the expected number of sections
    if len(sections) != 3:
        logging.error(f"Unexpected number of sections in forecast. Expected 3, got {len(sections)}.")
        return [s]

    try:
        # Split section 2 (Forecast) into sentences
        sentences = re.split(r'(?<=[.!?])\s+', sections[1])

        # Chunk section 2 respecting sentence boundaries
        section2_chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence
            else:
                section2_chunks.append(current_chunk.strip())
                current_chunk = sentence
        if current_chunk:
            section2_chunks.append(current_chunk.strip())

        # Assemble the final list of chunks
        chunks = [sections[0]] + section2_chunks + [sections[2]]

        # Add counters to the messages
        total_chunks = len(chunks)
        chunks_with_counters = [f"{idx + 1}/{total_chunks}\n{chunk}" for idx, chunk in enumerate(chunks)]

        while any([len(chunk) > 500 for chunk in chunks]):
            for idx, chunk in enumerate(chunks):
                if len(chunk) > 500:
                    half = len(chunk) // 2
                    chunks[idx:idx+1] = [chunk[:half], chunk[half:]]

        return chunks_with_counters
    except Exception as e:
        logging.error(f"Error while processing sections: {e}")
        return [s]


# --- Post to Mastodon ---
def post_toot(text):
    # last check of lentgh:
    if len(text) > 500:
        logging.info("Forecast too long, cancelling send")
        return
    else:
        m.toot(text)


def main():
    while True:
        try:  # Start of try block to catch any unexpected errors
            # Initiate cli screen
            global post_count
            clear_screen()
            post_time = datetime.now()
            logging.info("Starting weatherbot")
            print_banner()
            logging.info(f"Post number: {post_count}")

            # Get weather forecast
            logging.info("Getting weather forecast")
            forecast = openai_get_weather()

            # Post weather forecast
            logging.info("Posting weather forecast")
            if len(forecast) > 500:
                logging.info("Forecast too long, splitting into chunks")
                forecast_chunks = chunk_string_with_counters(forecast)
                
                valid_chunks = all([len(chunk) <= 500 for chunk in forecast_chunks])
                if not valid_chunks:
                    logging.error("One or more chunks are too long. Cancelling send.")
                    continue
                for forecast in forecast_chunks:
                    try:
                        logging.info("%d", len(forecast))
                        logging.info("Posting chunk")
                        post_toot(forecast)
                    except Exception as e:
                        logging.error(e)
                        continue
                logging.info("All chunks posted")
            else:
                logging.info("Posting forecast, under 500 characters")
                try:
                    logging.info("%d", len(forecast))
                    logging.info("Posting chunk")
                    post_toot(forecast)
                except Exception as e:
                    logging.error(e)
                    continue
            logging.info("Post completed")
            post_count += 1
            logging.info(post_time)
            next_post_time = post_time + timedelta(seconds=post_interval)
            logging.info(f"Sleeping until {next_post_time}")
            time.sleep(post_interval)

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(post_interval)



if __name__ == "__main__":
    main()
