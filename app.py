import streamlit as st
import re
from groq import Groq


st.set_page_config(page_title="AI Legal Query Assistant", page_icon="⚖️")

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
You are a Legal Information Assistant.

STRICT RULES (follow all):

1. Answer ONLY the exact question asked by the user.
2. If the question is vague, incomplete, or lacks necessary facts:
   - DO NOT provide a legal answer.
   - ONLY ask the user to clarify what information is missing.
3. DO NOT assume facts that the user has not stated.
4. DO NOT guess jurisdiction, country, or specific laws.
5. If the selected legal domain does not match the question, clearly point it out.
6. Provide ONLY general legal information, never legal advice.
7. Do NOT add extra explanations unless explicitly asked.
8. Use simple, non-technical language.

If information is insufficient, say:
"It is not possible to provide an answer without more details."

"""



USER_TEMPLATE = """
User selected legal domain: {domain}

User question:
"{question}"

TASK:
1. First, briefly restate the user's question in one sentence.
2. Answer ONLY that question.
3. Use simple, non-technical language.
4. If the question lacks required information, clearly state what is missing.
5. If the domain selection appears incorrect, mention it.
6. Do NOT include unrelated legal explanations.
7. End with:
"""

def domain_seems_mismatched(domain, question):
    employment_keywords = ["job", "company", "employer", "salary", "fired", "terminated"]
    consumer_keywords = ["product", "order", "refund", "seller", "online", "damaged"]

    q = question.lower()

    if domain == "Consumer Rights" and any(k in q for k in employment_keywords):
        return True
    if domain == "Employment Law" and any(k in q for k in consumer_keywords):
        return True

    return False

def generate_legal_answer(domain, question):
    # ---------- HARD STOP FOR VAGUE QUESTIONS ----------
    generic_patterns = [
        r"\bcan i take legal action\b",
        r"\bwhat are my rights\b",
        r"\bis this legal\b",
        r"\bcan i sue\b",
        r"\blegal action\b"
]
    normalized_question = question.strip().lower()
    for pattern in generic_patterns:
        if re.match(pattern, normalized_question):
            return (
                "This question is too general to answer.\n\n"
                "Please describe what happened, who was involved, and what issue you are facing "
                "so that general legal information can be shared.\n\n"
                "This is general legal information, not legal advice. "
                "Please consult a qualified lawyer for your specific situation."
    )

        if not question or len(question.strip()) < 8:
            return "Please provide a clearer legal question with more details."

    # HARD STOP FOR DOMAIN MISMATCH
    if domain_seems_mismatched(domain, question):
        return (
            f"The selected domain is '{domain}', but the question appears to relate to a different "
            "area of law.\n\n"
            "Please select the correct legal domain or clarify your question.\n\n"
            "This is general legal information, not legal advice."
        )

    alignment_instruction = f"""
IMPORTANT INSTRUCTIONS:
- Answer ONLY the user's exact question.
- Do NOT add unrelated legal information.
- Do NOT assume missing facts.
- If the selected domain ({domain}) does not match the question, clearly say so.
- If the information provided is insufficient, explicitly say that.
- Use simple, non-technical language.
"""

    user_prompt = USER_TEMPLATE.format(
        domain=domain,
        question=question
    )

    final_prompt = alignment_instruction + "\n\n" + user_prompt

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": final_prompt}
        ],
        temperature=0.1,
        max_tokens=500
    )

    
    raw_answer = response.choices[0].message.content.strip()

    final_answer = (
        raw_answer
        + "\n\n"
        + "This is general legal information, not legal advice. "
          "Please consult a qualified lawyer for your specific situation."
    )

    return final_answer





# ---------- STREAMLIT CHAT UI ----------



st.title(" AI-Powered Legal Query Assistant")
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
            answer = generate_legal_answer(domain, user_input)

            st.markdown(answer)

    # Save assistant response in history
    st.session_state.messages.append({"role": "assistant", "content": answer})

# Clear chat button
if st.sidebar.button("Clear conversation"):
    st.session_state.messages = []
    st.rerun()
