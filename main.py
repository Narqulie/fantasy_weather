import openai
from mastodon import Mastodon
import logging
import time
import json

# Logging
logging.basicConfig(filename='weatherbot.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

# Read config
try:
    with open('config.json') as f:
        config = json.load(f)

        mastodon_access_token = config['mastodon_access_token']
        mastodon_base_url = config['mastodon_base_url']

        openai_api_key = config['openai_api_key']
        openai_prompt = config['openai_prompt']
        openai_max_tokens = config['max_tokens']
        openai_temperature = config['temperature']
except Exception as e:
    logging.error(e)
    exit()


# OpenAI setup
openai.api_key = openai_api_key
openai.prompt = openai_prompt
openai.max_tokens = openai_max_tokens
openai.temperature = openai_temperature

# Mastodon API setup
m = Mastodon(access_token=mastodon_access_token,
             api_base_url=mastodon_base_url)


# Functions
# --- Get weather forecast from OpenAI ---
def openai_get_weather():
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user",
                  "content": openai_prompt}])
    forecast = completion.choices[0].message.content
    logging.info(forecast)
    logging.info(len(forecast))
    print(len(forecast))
    return forecast


# --- Split string into chunks ---
def chunk_string_with_counters(s, chunk_size=500):
    # List to store the chunks
    chunks = []

    while s:
        # If the remaining string is less than chunk size, add it to chunks
        if len(s) <= chunk_size:
            chunks.append(s)
            break

        # Find the last sentence-ending punctuation before the chunk limit
        split_at = s.rfind('\n', 0, chunk_size)
        if split_at == -1:
            split_at = s.rfind('!', 0, chunk_size)
        if split_at == -1:
            split_at = s.rfind('?', 0, chunk_size)

        # If no suitable split point found, split at the chunk limit
        split_at = split_at + 1 if split_at != -1 else chunk_size

        # Add chunk to the list and continue with the remainder
        chunks.append(s[:split_at].strip())
        s = s[split_at:].strip()

    # Add counters to the messages
    total_chunks = len(chunks)
    chunks_with_counters = [f"{idx + 1}/{total_chunks}\n{chunk}" for idx,
                            chunk in enumerate(chunks)]

    return chunks_with_counters


# --- Post to Mastodon ---
def post_toot(text):
    m.toot(text)


# --- Main ---
def main():
    logging.info("Starting weatherbot")

    while True:
        logging.info("Getting weather forecast")
        forecast = openai_get_weather()

        logging.info("Posting weather forecast")
        if len(forecast) > 500:
            logging.info("Forecast too long, splitting into chunks")
            forecast_chunks = chunk_string_with_counters(forecast)
            for forecast in forecast_chunks:
                try:
                    logging.info("%d %s", len(forecast), forecast)
                    logging.info("Posting chunk")
                    post_toot(forecast)
                except Exception as e:
                    logging.error(e)
                    break
            logging.info("All chunks posted")
        else:
            logging.info("Posting forecast, under 500 characters")
            try:
                logging.info("%d %s", len(forecast), forecast)
                logging.info("Posting chunk")
                post_toot(forecast)
            except Exception as e:
                logging.error(e)
                pass
        logging.info("Post completed")
        logging.info("Sleeping for 2 hours")
        time.sleep(3600*2)


# --- Run ---
main()
