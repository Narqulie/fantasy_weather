# 🌌 Zorblerg's Weatherbot for Mastodon

**Zorblerg's Weatherbot** is an enchanting bot that fetches and posts whimsical weather forecasts from mystical realms to Mastodon. Powered by OpenAI's GPT-3.5-turbo model, it conjures up forecasts that are not only fantastical but also a delight to read.

## Features

- **Whimsical Forecasts**: Utilizes the prowess of OpenAI to generate imaginative weather predictions.
- **Intelligent Chunking**: For those especially detailed forecasts, the bot smartly breaks them down into manageable, readable chunks before posting.
- **Regular Updates**: Without missing a beat, Zorblerg posts to Mastodon at consistent intervals, ensuring that the denizens of your timeline are always informed about the ethereal weather patterns.
- **Configurable**: Tailor the bot's behavior using the `config.json` file. From the prompt to the posting frequency, make it truly yours.

## Overview

- `openai_get_weather()`: Fetches a fantastical weather forecast from OpenAI.
- `chunk_string_with_counters()`: Splits long forecasts into readable chunks, ensuring no forecast is cut mid-sentence.
- `post_toot()`: Posts the forecast (or its chunks) to Mastodon.
- `main()`: The core loop, orchestrating the fetching, processing, and posting of forecasts.

Should you wish to peer into the mystical code that powers Zorblerg, dive right in. And remember, in every line and function, there's a sprinkle of magic waiting to be discovered.

---