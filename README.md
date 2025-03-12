# Medical Assistant Discord Bot

A specialized Discord bot that provides medical information assistance using Mistral AI, with support for patient records, insurance information, and medical data retrieval.

## Features

- **RAG (Retrieval Augmented Generation)** 
  - FAISS-powered similarity search
  - Intelligent chunking of insurance information
  - Cached embeddings for performance

- **Medical Data Access**
  - Patient information retrieval
  - Allergy information
  - Diagnostic reports
  - Medical conditions
  - ICD-10 code assistance

- **Caching System**
  - Redis caching for responses (1-hour TTL)
  - File-based caching for embeddings and chunks
  - Efficient response retrieval

- **FHIR Integration**
  - Epic FHIR API client
  - Secure JWT authentication
  - Comprehensive medical data parsing

## Setup

### Prerequisites
- Python 3.8+
- Redis server
- Conda package manager

### Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create and activate conda environment:
```bash
conda env create -f local_env.yml
conda activate discord_bot
```

3. Create a `.env` file with your credentials:
```
DISCORD_TOKEN="your-discord-token"
MISTRAL_API_KEY="your-mistral-api-key"
EPIC_TOKEN_URL="your-epic-token-url"
PRIVATE_KEY_PATH="path-to-your-private-key"
```

### Discord Bot Setup

1. Create a new Discord application at https://discord.com/developers
2. Enable required intents:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
3. Copy the bot token to your `.env` file

### Mistral AI Setup

1. Sign up at https://console.mistral.ai
2. Generate an API key
3. Add the API key to your `.env` file

## Usage

1. Start the bot:
```bash
python bot.py
```

2. The bot will respond to messages in channels it has access to
3. Medical data queries will automatically retrieve relevant information
4. Insurance information is processed using RAG for accurate responses

## Architecture

- `bot.py`: Main Discord bot implementation
- `agent.py`: Mistral AI integration and RAG system
- `python/`: 
  - `patient_info_parser.py`: FHIR patient data parser
  - `insurance_parser.py`: Insurance information parser
  - `epic_fhir_client.py`: Epic FHIR API client
  - `parse_diagnostic_data.py`: Diagnostic report parser
  - `condition_parser.py`: Medical condition parser
  - `allergy_parser.py`: Allergy information parser

## Security

- JWT-based authentication for EPIC FHIR API
- Environment variables for sensitive credentials
- Redis TTL for cached responses
- Secure private key handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For support, please open an issue in the repository or contact Olivia Beyer Bruvik or Neel Narayan.
