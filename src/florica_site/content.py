"""Site content and navigation in one reviewable place."""

SITE = {
    "name": "Florica Ltd",
    "origin": "https://floricaltd.github.io",
    "copyright_year": "2026",
    "email": "hello@floricaltd.com",
    "description": (
        "Florica Ltd helps ambitious teams turn AI and technology into practical, "
        "secure products and measurable operational gains."
    ),
}

NAVIGATION = (
    ("What we do", "/#services"),
    ("Products", "/#products"),
    ("How we work", "/#approach"),
    ("About", "/about/"),
)

SERVICES = (
    {
        "number": "01",
        "title": "AI strategy & adoption",
        "text": "Find the valuable use cases, set clear guardrails, and move from experimentation to an operating plan your teams can deliver.",
        "tags": ("Opportunity mapping", "AI governance", "Adoption roadmaps"),
    },
    {
        "number": "02",
        "title": "Intelligent automation",
        "text": "Redesign repetitive workflows around people, data, and AI agents—without losing the controls that keep your business dependable.",
        "tags": ("Agentic workflows", "Process redesign", "System integration"),
    },
    {
        "number": "03",
        "title": "Digital product engineering",
        "text": "Design and build customer-facing products, internal platforms, and prototypes that prove value early and scale cleanly.",
        "tags": ("Product discovery", "Rapid prototyping", "Cloud delivery"),
    },
    {
        "number": "04",
        "title": "Data foundations",
        "text": "Make critical information usable and trusted, from pragmatic data architecture to retrieval systems built for modern AI applications.",
        "tags": ("Data readiness", "Knowledge systems", "Responsible AI"),
    },
)

PRODUCTS = (
    {
        "eyebrow": "2 weeks · fixed scope",
        "title": "AI Opportunity Sprint",
        "text": "A focused assessment that turns business friction into a ranked portfolio of feasible AI opportunities, with value, risk, and next steps made explicit.",
        "outcome": "Leave with a board-ready opportunity map and 90-day action plan.",
    },
    {
        "eyebrow": "Private knowledge assistant",
        "title": "Florica Knowledge Copilot",
        "text": "A secure, source-grounded assistant that helps teams find trusted answers across policies, projects, and operational knowledge.",
        "outcome": "Reduce search time while keeping sources, permissions, and human judgment visible.",
    },
    {
        "eyebrow": "Reusable automation patterns",
        "title": "Workflow Accelerator",
        "text": "A configurable foundation for human-in-the-loop AI workflows, built to connect with the tools your teams already use.",
        "outcome": "Launch the first controlled workflow quickly, then extend it without starting over.",
    },
)

PRINCIPLES = (
    ("Value before novelty", "We start with the business outcome, not a fashionable tool."),
    ("Small teams, senior attention", "The people shaping the answer stay close to delivery."),
    ("Built for trust", "Security, explainability, and operational ownership are designed in."),
    ("Capability that stays", "We work with your team and leave behind systems and confidence."),
)
