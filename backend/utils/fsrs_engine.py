from __future__ import annotations

from datetime import datetime, timezone

from fsrs import Card, Rating, Scheduler

from backend.utils import skill_graph

_scheduler = Scheduler()

RATING_NAMES = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def new_card_state() -> dict:
    return Card().to_dict()


def review(card_state: dict, rating: int) -> tuple[dict, dict]:
    if rating not in RATING_NAMES:
        raise ValueError(f"FSRS rating must be 1-4, got {rating}")
    card = Card.from_dict(card_state)
    new_card, log = _scheduler.review_card(card, Rating(rating), review_datetime=_now())
    return new_card.to_dict(), log.to_dict()


def retrievability(card_state: dict) -> float:
    return round(Card.from_dict(card_state).get_retrievability(_now()), 3)


def is_due(card_state: dict) -> bool:
    due = datetime.fromisoformat(card_state["due"])
    return due <= _now()


_FAMILY_BLURBS = {
    "Data Structures & Algorithms": "the core toolkit interviewers probe hardest",
    "Programming & Development": "the everyday craft everything else sits on top of",
    "Software Design": "how individual pieces become a system that holds together",
    "Data & Databases": "how information is shaped, stored and retrieved at scale",
    "Machine Learning": "how a model learns a pattern instead of being told the rule",
    "Deep Learning": "how layered models learn representations directly from raw data",
    "Statistics & Analytics": "how to read evidence in numbers without fooling yourself",
    "Aptitude & Placement": "the timed-test layer almost every Indian campus drive opens with",
    "Career Readiness": "how the work gets seen and judged by someone outside the team",
}


def _family_blurb(family: str) -> str:
    return _FAMILY_BLURBS.get(family, "a building block the rest of the track leans on")


def _card_for_skill(skill_id: str, archetype: str) -> dict | None:
    info = skill_graph.node(skill_id)
    name = info["name"]
    family = info["family"]
    prereqs = skill_graph.prerequisites(skill_id)
    children = skill_graph.unlocks(skill_id)

    if archetype == "definition":
        front = f"In your plan, where does \"{name}\" sit and what is it for?"
        back = (f"It belongs to {family} - {_family_blurb(family)}. "
                f"Scoped at about {info['estimated_hours']} focused hours, "
                f"Bloom level {info['bloom_level']} of 6.")
    elif archetype == "prerequisite":
        if not prereqs:
            return None
        prereq_names = ", ".join(skill_graph.node(p)["name"] for p in prereqs[:3])
        front = f"Before \"{name}\" earns its place, what should already be solid?"
        back = f"{prereq_names}. Skipping ahead here is the most common reason this topic feels harder than it should."
    elif archetype == "unlock":
        if not children:
            return None
        child_names = ", ".join(skill_graph.node(c)["name"] for c in children[:3])
        front = f"Once \"{name}\" clicks, what does it directly open up?"
        back = f"{child_names}. That is the next legitimate step - no detours needed."
    else:
        return None

    return {"skill_id": skill_id, "front": front, "back": back}


def build_deck(skill_ids: list[str], limit: int = 24) -> list[dict]:
    archetypes = ["definition", "prerequisite", "unlock"]
    cards: list[dict] = []
    for index, skill_id in enumerate(skill_ids):
        if len(cards) >= limit:
            break
        order = archetypes[index % len(archetypes):] + archetypes[:index % len(archetypes)]
        for archetype in order:
            card = _card_for_skill(skill_id, archetype)
            if card is not None:
                cards.append(card)
                break
    return cards
