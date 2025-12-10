import streamlit as st
from groq import Groq

# ---------- LLM CLIENT ----------


@st.cache_resource
def get_client():
    """
    Create and cache the Groq client.
    Reads API key from Streamlit secrets (local secrets.toml or Cloud secrets).
    """
    api_key = st.secrets["GROQ_API_KEY"]
    return Groq(api_key=api_key)


client = get_client()

# ---------- FAQ DATA (EXAMPLES) ----------

# Some example FAQs for each domain – just to show you collected & categorized them.
FAQ_DATA = {
    "Consumer Rights": [
        {
            "question": "What can I do if a product I bought is defective and the seller refuses to replace it?",
            "answer": "Generally, consumers can raise a complaint with the seller, escalate to the company, and, if unresolved, approach a consumer dispute redressal forum or similar authority. Keep all bills and written communication as proof."
        },
        {
            "question": "Can a shop refuse to give me a bill?",
            "answer": "In many jurisdictions, sellers are expected or required to provide an invoice or bill. A bill is useful as proof of purchase in case of disputes or warranty claims."
        },
    ],
    "Employment Law": [
        {
            "question": "Can my employer fire me without notice?",
            "answer": "In many places, termination rules depend on the employment contract and local labour laws. Often there are notice-period requirements, but there can be exceptions such as misconduct or probation periods."
        },
        {
            "question": "Am I entitled to overtime pay?",
            "answer": "Eligibility for overtime pay depends on local labour laws and the type of employment. Some workers are entitled to extra pay for hours beyond the standard work week."
        },
    ],
    "Cyber Law": [
        {
            "question": "What should I do if someone is harassing me online?",
            "answer": "You can collect evidence (screenshots, messages), block or report the account on the platform, and in serious cases consider filing a complaint with cybercrime authorities or the police."
        },
        {
            "question": "Is it legal to share someone’s private chat screenshots publicly?",
            "answer": "Sharing private communications without consent may violate privacy laws, platform policies, or defamation laws, depending on what is shared and local regulations."
        },
    ],
    "Civil Matters": [
        {
            "question": "What is a civil case?",
            "answer": "A civil case usually involves disputes between individuals or organizations about rights, money, property, or contracts rather than crimes."
        },
        {
            "question": "How long do civil cases typically take?",
            "answer": "Civil cases can take months or years depending on complexity, court workload, and procedural steps. Timelines vary widely by country and court."
        },
    ],
}


def build_faq_context(domain: str) -> str:
    """Build a short text context from FAQs for the selected domain."""
    faqs = FAQ_DATA.get(domain, [])
    if not faqs:
        return ""

    lines = [f"Example FAQs and generic answers for {domain}:"]
    for item in faqs:
        lines.append(f"- Q: {item['question']}")
        lines.append(f"  A: {item['answer']}")
    return "\n".join(lines)


# ---------- PROMPTS ----------

SYSTEM_PROMPT = """
You are an AI assistant that gives GENERAL INFORMATION about basic legal topics,
not personalised legal advice.

SAFETY & COMPLIANCE RULES (VERY IMPORTANT):
- You are NOT a lawyer and NOT a law firm.
- You do NOT create a lawyer–client relationship.
- You only provide high-level, generic information.
- You MUST NOT draft contracts, notices, petitions, or formal legal documents.
- You MUST NOT tell users exactly what they 'should' do in their specific case.
- If a question is complex, high-stakes, or depends on local law, say that they should consult a qualified advocate or legal professional in their jurisdiction.
- Laws differ by country and change over time. You should speak in general terms (e.g., 'in many places', 'often', 'typically') rather than asserting that something is definitely legal or illegal everywhere.
- If the user asks for help evading law, doing something illegal, or harming others, refuse and suggest seeking lawful options only.
- Always include a short disclaimer at the end: 'This is general information, not legal advice. Please consult a qualified lawyer for advice on your specific situation.'
"""

USER_TEMPLATE = """
User's selected legal domain: {domain}

Here are some example FAQs and generic answers for this domain (if any):
---
{faq_context}
---

Conversation so far (if any):
{chat_history}

User's new question:
"{question}"

TASK:
- Answer in simple, clear language.
- First, briefly identify which general area of law the question relates to and what the user seems to be asking.
- Provide general information, typical options, or processes that *may* apply in this kind of situation.
- Do NOT claim to know the exact law in the user's country or give final conclusions.
- Encourage the user to keep documents, screenshots, or written communication when relevant.
- If the question is vague or missing critical facts, say what extra information a lawyer would usually need.
- End with: 'This is general information, not legal advice. Please consult a qualified lawyer for advice on your specific situation.'
"""


def generate_legal_answer(domain: str, question: str, history: list) -> str:
    """Call the LLM to generate a safe, domain-aware legal answer."""

    # Build textual chat history for the prompt (user & assistant messages only)
    history_lines = []
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        if role in ("user", "assistant"):
            history_lines.append(f"{role.capitalize()}: {content}")
    history_text = "\n".join(history_lines) if history_lines else "No prior messages."

    faq_context = build_faq_context(domain)

    user_prompt = USER_TEMPLATE.format(
        domain=domain,
        faq_context=faq_context or "No FAQs available for this domain.",
        chat_history=history_text,
        question=question,
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        temperature=0.2,
        max_tokens=900,
    )

    return response.choices[0].message.content.strip()


# ---------- STREAMLIT CHAT UI ----------

st.set_page_config(page_title="AI Legal Query Assistant", page_icon="⚖️")

st.title("⚖️ AI-Powered Legal Query Assistant")
st.write(
    "Ask basic questions about **consumer rights, employment law, cyber law, or civil matters**.\n"
    "This tool gives **general information only** and is **not a substitute for professional legal advice**."
)

# Sidebar: domain selection & info
st.sidebar.header("Settings")
domain = st.sidebar.selectbox(
    "Select legal domain (approximate):",
    ["Consumer Rights", "Employment Law", "Cyber Law", "Civil Matters", "General / Not Sure"],
)

st.sidebar.markdown(
    """
**Note:**  
- Answers are generic and may not match the law in your country exactly.  
- For serious or urgent issues, please speak with a qualified lawyer.
"""
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Type your legal question here...")

if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = generate_legal_answer(domain, user_input, st.session_state.messages)
            st.markdown(answer)

    # Save assistant response in history
    st.session_state.messages.append({"role": "assistant", "content": answer})

# Clear chat button
if st.sidebar.button("Clear conversation"):
    st.session_state.messages = []
    st.rerun()
