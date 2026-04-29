"""Test the full answer_question pipeline with a follow-up."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from answer import answer_question

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

result = answer_question(
    "yes It was paid to Seneca college",
    history=history,
)

print("=" * 80)
print("REFUSED:", result["refused"])
print("BEST DISTANCE:", result["best_distance"])
print("SEARCH QUERY USED:", result.get("search_query_used"))
print("=" * 80)
print("ANSWER:")
print(result["answer"])