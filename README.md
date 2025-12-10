AI-Powered Legal Query Assistant

A Streamlit-based Generative AI chatbot that answers basic legal queries about consumer rights, civil matters, cyber law, and employment law.
It uses Groq + Llama 3 to generate safe, high-level legal information.

Features

Chat-style interface (Streamlit)

Legal domain selection sidebar

Safety-focused prompting

FAQ-based context enhancement

Clear, simple, non-advisory responses

Disclaimer enforcement

No API key revealed on UI

Project Structure
legal-query-assistant
│ app.py
│ requirements.txt
│ README.md
└── .streamlit (local only, contains secrets.toml — NOT uploaded)
└── venv (ignored)

Technologies Used

Python

Streamlit

Groq API

Llama 3.1 (8B Instant)

Prompt Engineering

Secrets

Create a .streamlit/secrets.toml (do NOT upload):

GROQ_API_KEY = "your_api_key_here"

Run Locally
pip install -r requirements.txt
streamlit run app.py
