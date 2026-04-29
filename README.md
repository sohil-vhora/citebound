# 📌 Citebound

A citation-grounded Q&A assistant for international students in Canada — covering immigration, tax basics, and provincial health coverage. Every answer cites a `canada.ca` or provincial government source, or refuses honestly.

> **⚠️ Research project — not legal, immigration, or tax advice.** For your specific situation, consult a Regulated Canadian Immigration Consultant via [college-ic.ca](https://college-ic.ca) or a Canadian immigration lawyer. All decisions on immigration applications are made solely by IRCC.

## Why this exists

International students in Canada navigate a fragmented and rapidly changing information landscape. Between November 2024 and January 2026 alone, IRCC made significant rule changes affecting study permit caps, off-campus work hours, the PGWP field-of-study list, spousal open work permits, LMIA-based CRS points, the Provincial Attestation Letter exemption for graduate students, and Quebec's PEQ closure. A general-purpose LLM trained before these changes will confidently produce wrong answers about every one of them.

Citebound is a research project exploring whether retrieval-augmented generation with strict citation discipline and explicit refusal architecture can produce trustworthy answers in a domain where wrong answers cost real people their status, their PR pathway, or their savings.

It is deliberately **information**, not **advice**. The boundary is informed by IRPA s. 91, which restricts immigration advice to authorized representatives (RCICs, lawyers, Quebec notaries). Citebound explains how rules work in general; it never tells a specific user whether they qualify or what they should do.

## What it does

- Answers questions about study permits, PGWP, off-campus work, Express Entry, PNPs, CRA tax basics for students, and provincial health coverage
- Cites a numbered source URL with last-modified date for every factual claim
- Refuses personal-prediction and pathway-recommendation questions ("will I get an ITA?", "should I apply through OINP or CEC?")
- Refuses out-of-scope questions instead of inventing answers
- Refuses honestly when the corpus genuinely lacks a current source
- Handles conversational follow-ups via LLM-based query rewriting

## What it doesn't do

- Predict outcomes for specific users
- Recommend application strategies
- Tell users whether they personally qualify
- Replace authorized immigration representatives or tax professionals

## Architecture

```text
Question → Query rewriter (Haiku, only for follow-ups)
→ Personal-prediction detector (heuristic)
→ If detected: route to LLM with refusal-first framing
→ Else: vector retrieval over canada.ca / provincial corpus (Voyage embeddings + ChromaDB)
→ If best distance > 1.20: refuse honestly
→ Else: Claude Opus 4.7 with citation-required system prompt
→ Answer with inline citations + source cards + freshness badges
```

**Two-layer refusal:**

1. **Heuristic intent layer** catches personal-prediction phrasing ("will I get," "am I eligible," "should I apply") and routes those questions through the LLM with refusal-first framing, regardless of retrieval confidence.
2. **Distance threshold layer** catches off-corpus questions and refuses rather than letting the model fall back to training data.

See [`EVALS.md`](EVALS.md) for evaluation methodology and current results.

## Stack

- **LLM**: Claude Opus 4.7 (answers) + Claude Haiku 4.5 (query rewriting)
- **Embeddings**: voyage-3
- **Vector store**: ChromaDB (local persistent)
- **UI**: Streamlit with custom theming
- **Corpus**: 45 sources from canada.ca, ontario.ca, quebec.ca, alberta.ca, bc.gov, novascotia.ca, manitoba.gov, ircc.canada.ca, ramq.gouv.qc.ca

## Eval results

| Category   | Passed | Total | Pass rate |
|------------|--------|-------|-----------|
| factual    | 8      | 9     | 88.9%     |
| refusal    | 3      | 3     | 100%      |
| scope      | 2      | 2     | 100%      |
| freshness  | 1      | 1     | 100%      |
| **Overall**| **14** | **15**| **93.3%** |

The single failure is a documented retrieval-bridging limitation (the user queries a deprecated program name; the corpus indexes only its replacement). See [`EVALS.md`](EVALS.md) for details and the deferred fix.

## Running locally

Requires Python 3.11+, an Anthropic API key, and a Voyage AI API key.

```bash
# Clone and set up
git clone https://github.com/sohil-vhora/citebound.git
cd citebound
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# Add your API keys to a .env file
# ANTHROPIC_API_KEY=sk-ant-...
# VOYAGE_API_KEY=pa-...

# Build the corpus (run once)
python scripts/scrape.py
python scripts/chunk_and_embed.py

# Run the app
streamlit run app.py

# Or run evals
python evals/run_evals.py

```

## Project structure

```markdown
citebound/
├── app.py                    # Streamlit chat UI
├── scripts/
│   ├── sources.py            # Authoritative URL list (45 sources)
│   ├── scrape.py             # Scraper with date_modified extraction
│   ├── chunk_and_embed.py    # Token-aware chunking + Voyage embeddings
│   └── answer.py             # Two-layer refusal + retrieval + LLM
├── evals/
│   ├── test_cases.py         # 15 test cases across 4 categories
│   ├── run_evals.py          # Eval runner with CSV/JSON output
│   └── results/              # Per-run results (gitignored)
├── corpus/                   # Scraped JSON, one per source
├── vector_db/                # ChromaDB persistent store (gitignored)
├── EVALS.md                  # Evaluation methodology and results
└── README.md                 # This file
```

## Design principle

Citebound provides **information**, not **advice**. Every answer cites a canonical source. The system refuses to render verdicts on individual eligibility — that determination belongs to IRCC and authorized representatives. This boundary is informed by IRPA s. 91 and is preserved even in profile-aware retrieval contexts: the system can personalize *which rules apply* to a user's situation without telling them whether they qualify.

## Acknowledgements

Source landscape derived from a research report on the Canadian international-student information ecosystem, regulatory analysis under IRPA s. 91, and the College of Immigration and Citizenship Consultants' public guidance.

## License

This is a research/portfolio project. Source content cited from canada.ca and provincial government sites remains the property of the Government of Canada and respective provincial governments under the [Government of Canada open licence](https://open.canada.ca/en/open-government-licence-canada).


