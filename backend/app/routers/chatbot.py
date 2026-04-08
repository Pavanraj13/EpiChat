from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random
import re

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

class ChatRequest(BaseModel):
    message: str

# Clinical knowledge base for keyword-based expert system
KNOWLEDGE_BASE = {
    r"(seizure|epileptic|fit)": [
        "A seizure is a sudden, uncontrolled electrical disturbance in the brain. It can cause changes in your behavior, movements or feelings, and in levels of consciousness.",
        "Epileptic activity is typically identified by high-amplitude spikes or sharp waves in the EEG recording.",
        "If you suspect a seizure is occurring, ensure the person is in a safe space and time the duration of the event."
    ],
    r"(eeg|scan|brain wave)": [
        "EEG (Electroencephalogram) measures the electrical activity of your brain using electrodes. Our AI analyzes 18 channels to find abnormalities.",
        "The model looks for 'spikes' and 'spike-and-wave' complexes which are hallmarks of epilepsy.",
        "Normal background activity usually consists of Alpha and Beta waves depending on whether you are awake or relaxed."
    ],
    r"(help|first aid|emergency)": [
        "If someone is having a seizure: 1. Keep them safe (clear the area). 2. Do NOT put anything in their mouth. 3. Turn them on their side. 4. Call medical services if it lasts >5 mins.",
        "Always stay calm. Most seizures end on their own within a minute or two.",
        "For non-emergency support, you can reach out to your assigned physician via the 'Contact Physician' button in your dashboard."
    ],
    r"(absent|absence)": [
        "Absence seizures (formerly 'petit mal') involve brief, sudden lapses of consciousness. They look like the person is staring into space.",
        "On an EEG, absence seizures often show a characteristic 3 Hz spike-and-wave pattern."
    ],
    r"(medication|keppra|medicine|pill)": [
        "Anti-epileptic drugs (AEDs) like Levetiracetam (Keppra) help stabilize the brain's electrical activity.",
        "It is critical to take your medication at the same time every day to maintain steady levels in your bloodstream.",
        "Never stop taking your medication without consulting your neurologist first, as this can trigger a breakthrough seizure."
    ],
    r"(hello|hi|hey)": [
        "Hello! I am your EpiChat AI assistant. I can help interpret EEG basics or provide epilepsy information. How can I assist you?",
        "Hi there! How can I help you with your brain health tracking today?"
    ]
}

DEFAULT_RESPONSES = [
    "I'm here to help with epilepsy information. Could you please specify if you're asking about EEG results, seizure types, or medication safety?",
    "That's an interesting question. While I am an AI assistant, I recommend discussing specific clinical symptoms with your neurologist.",
    "I understand. To give you the best information, I focus on EEG interpretation and epilepsy care basics."
]

@router.post("")
async def chat_with_ai(request: ChatRequest):
    user_msg = request.message.lower()
    
    # Simple keyword search
    for pattern, responses in KNOWLEDGE_BASE.items():
        if re.search(pattern, user_msg):
            return {"text": random.choice(responses)}
            
    return {"text": random.choice(DEFAULT_RESPONSES)}
