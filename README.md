# Bipkit Python SDK

Official Python SDK for the [Bipkit System One Decision Engine API](https://docs.bipkit.io).

## Installation

```bash
pip install bipkit
```

Optional extras:

```bash
# LangChain / LangGraph classifier, model router, and guardrail middleware
pip install "bipkit[langchain]"

# Offline Ed25519 Decision Provenance Ledger (DPL) bundle verification
pip install "bipkit[dpl]"
```

## Quickstart

```python
from bipkit import Bipkit, should_escalate

# Reads BIPKIT_API_KEY from environment by default
client = Bipkit()

decision = client.decide(
    state="Customer asks to cancel their enterprise contract and requests a refund.",
    choices=[
        {"id": "billing_retention", "label": "Billing & Retention"},
        {"id": "technical_support", "label": "Technical Support"},
        {"id": "sales_inquiry", "label": "Sales Inquiry"},
    ],
    engine="bip-cascade",
)

print("Top choice:", decision.top_choice)
if should_escalate(decision):
    print("Low confidence — escalate to System Two LLM")
```

## Async Usage

```python
import asyncio
from bipkit import AsyncBipkit

async def main() -> None:
    async with AsyncBipkit() as client:
        engines = await client.engines.list()
        print([e.name for e in engines])

asyncio.run(main())
```

## LangChain / Agent Middleware

```python
from bipkit.integrations.langchain import (
    BipkitClassifier,
    BipkitModelRouterMiddleware,
    BipkitGuardrailMiddleware,
    ModelChoice,
)

classifier = BipkitClassifier(engine="bip-instant")
router = BipkitModelRouterMiddleware(
    choices={
        "fast": ModelChoice(model="gpt-4o-mini", criteria="Simple factual or formatting tasks"),
        "deep": ModelChoice(model="o3", criteria="Complex architecture or multi-step reasoning"),
    },
    classifier=classifier,
)
selected_model = router.route("Summarize this 2-sentence email.")
```

## Documentation & Support

- API Documentation: [https://docs.bipkit.io](https://docs.bipkit.io)
- Support: `support@bipware.co.za`
