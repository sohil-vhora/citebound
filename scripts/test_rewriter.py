"""Quick test of the query rewriter on a real follow-up scenario."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from answer import rewrite_followup_to_standalone, get_clients

_, _, anthropic = get_clients()

history = [
    {
        "role": "user",
        "content": (
            "If I have tuition credits in my tax file from previous years and "
            "I have moved to canada in 2023, can I use it in Federal as well "
            "as Provincial tax payments"
        ),
    },
    {
        "role": "assistant",
        "content": "I don't have a current source that directly answers...",
    },
]
question = "yes It was paid to Seneca college"

rewritten = rewrite_followup_to_standalone(question, history, anthropic)
print("ORIGINAL:  ", question)
print("REWRITTEN: ", rewritten)