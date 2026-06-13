"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return None

try:
    from groq import Groq
except ImportError:
    Groq = None

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    if Groq is None:
        raise RuntimeError("groq package not installed. Install it to use the LLM client.")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _format_price(price: float | int | None) -> str:
    if price is None:
        return "a great price"
    if isinstance(price, float) and price.is_integer():
        return f"${int(price)}"
    return f"${price:.2f}"


def _excerpt_text(listing: dict) -> str:
    parts = [
        listing.get("title", ""),
        listing.get("description", ""),
        listing.get("category", ""),
        " ".join(listing.get("style_tags", [])),
        listing.get("brand", "") or "",
        listing.get("platform", ""),
    ]
    return " ".join(parts).lower()


def _score_wardrobe_match(item: dict, target_styles: set[str], target_colors: set[str]) -> int:
    score = 0
    item_styles = {tag.lower() for tag in item.get("style_tags", [])}
    item_colors = {color.lower() for color in item.get("colors", [])}
    score += len(item_styles.intersection(target_styles)) * 2
    score += len(item_colors.intersection(target_colors))
    return score


def _choose_best_item(items: list[dict], category: str, target_styles: set[str], target_colors: set[str]) -> dict | None:
    candidates = [item for item in items if item.get("category") == category]
    if not candidates:
        return None
    scored = [(_score_wardrobe_match(item, target_styles, target_colors), item) for item in candidates]
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("name", "")))
    return scored[0][1] if scored[0][0] > 0 else candidates[0]


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description:  Keywords describing what the user is looking for (e.g., "vintage graphic tee").
        size:  Size string to filter by, or None to skip size filtering. Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:  Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of up to 3 dictionaries sorted by relevance (best match first).
        Each dictionary maps a single key containing the item description and
        price to a value dict with the item's platform and condition.
        Returns an empty list if nothing matches — does NOT raise an exception.

    Example output:
        [
            {
                "Vintage graphic tee, $24.00": {
                    "platform": "depop",
                    "condition": "good"
                }
            },
            ...
        ]

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    if not description or not description.strip():
        return []

    listings = load_listings()
    query_tokens = _tokenize(description)
    filtered = []

    normalized_size = size.strip().lower() if size else None
    for listing in listings:
        if max_price is not None and listing.get("price", float("inf")) > max_price:
            continue

        if normalized_size:
            listing_size = listing.get("size", "").lower()
            if normalized_size not in listing_size:
                continue

        listing_text = _excerpt_text(listing)
        title_tokens = _tokenize(listing.get("title", ""))
        score = sum(1 for token in query_tokens if len(token) > 1 and not token.isdigit() and token in listing_text)

        # Prefer results where the title contains an exact query keyword.
        # This makes actual jackets rank above related items like shackets.
        exact_title_matches = sum(1 for token in query_tokens if len(token) > 1 and not token.isdigit() and token in title_tokens)
        score += exact_title_matches * 5

        if score > 0:
            filtered.append({"score": score, "listing": listing})

    filtered.sort(key=lambda item: (-item["score"], item["listing"].get("price", 0)))
    if not filtered:
        return []

    results = []
    for item in filtered[:3]:
        listing = item["listing"]
        description = listing.get("description", "").strip()
        price = listing.get("price")
        price_text = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
        key = f"{description}, {price_text}"
        results.append({
            key: {
                "platform": listing.get("platform"),
                "condition": listing.get("condition"),
            }
        })

    if len(results) in (1, 2):
        print(f"I only found {len(results)} entr{'y' if len(results)==1 else 'ies'} that matched your search criteria.")

    return results


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.
    """

    def _resolve_listing(item: dict) -> dict:
        if not isinstance(item, dict):
            return {}

        if "category" in item or "title" in item or "style_tags" in item:
            return item

        if len(item) == 1 and isinstance(next(iter(item.values())), dict):
            listing_text = next(iter(item.keys()))
            extracted = {
                "title": listing_text,
                "description": listing_text,
            }
            extracted.update(next(iter(item.values())))
            return extracted

        return item

    def _infer_category(name: str) -> str:
        name = (name or "").lower()
        if any(keyword in name for keyword in ["jacket", "coat", "blazer", "parka", "outerwear", "trench"]):
            return "outerwear"
        if any(keyword in name for keyword in ["jean", "pant", "trouser", "skirt", "short", "cargo", "legging"]):
            return "bottoms"
        if any(keyword in name for keyword in ["shoe", "sneaker", "boot", "heel", "loafer", "sandal", "trainer"]):
            return "shoes"
        if any(keyword in name for keyword in ["dress", "romper", "jumpsuit"]):
            return "tops"
        return ""

    try:
        listing = _resolve_listing(new_item)
        wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
        item_name = listing.get("title") or listing.get("description") or "this piece"
        category = (listing.get("category") or _infer_category(item_name)).lower()
        new_item_styles = {tag.lower() for tag in listing.get("style_tags", []) if isinstance(tag, str)}
        new_item_colors = {color.lower() for color in listing.get("colors", []) if isinstance(color, str)}

        if not wardrobe_items:
            style_note = (
                f" with {', '.join(new_item_styles)}" if new_item_styles else ""
            )
            return (
                f"{item_name} is a great find{style_note}. "
                "I’d style it with clean, neutral basics, a simple shoe, and one standout accessory to keep the look balanced."
            )

        best_top = _choose_best_item(wardrobe_items, "tops", new_item_styles, new_item_colors)
        best_bottom = _choose_best_item(wardrobe_items, "bottoms", new_item_styles, new_item_colors)
        best_outerwear = _choose_best_item(wardrobe_items, "outerwear", new_item_styles, new_item_colors)
        best_shoes = _choose_best_item(wardrobe_items, "shoes", new_item_styles, new_item_colors)
        best_accessory = _choose_best_item(wardrobe_items, "accessories", new_item_styles, new_item_colors)

        suggestions: list[str] = []

        if category == "tops":
            if best_bottom and best_shoes:
                suggestions.append(
                    f"Pair {item_name} with {best_bottom['name']} and finish with {best_shoes['name']} for a polished look."
                )
            elif best_bottom:
                suggestions.append(f"Pair {item_name} with {best_bottom['name']} and keep the accessories minimal.")
            elif best_shoes:
                suggestions.append(f"Wear {item_name} with clean shoes like {best_shoes['name']} and a simple bottom.")
            else:
                suggestions.append(f"Style {item_name} with a fitted bottom and a statement accessory.")
        elif category == "bottoms":
            if best_top and best_outerwear:
                suggestions.append(
                    f"Wear {best_top['name']} with {item_name} and add {best_outerwear['name']} for a complete outfit."
                )
            elif best_top:
                suggestions.append(f"Wear {best_top['name']} with {item_name} and keep the rest of the accessories clean.")
            elif best_outerwear:
                suggestions.append(f"Pair {item_name} with a simple top and layer on {best_outerwear['name']}.")
            else:
                suggestions.append(f"Style {item_name} with a fitted top and tonal shoes for a balanced look.")
        elif category == "outerwear":
            if best_top and best_bottom:
                suggestions.append(
                    f"Layer {item_name} over {best_top['name']} and {best_bottom['name']} for an easy outfit."
                )
            elif best_top:
                suggestions.append(f"Layer {item_name} over {best_top['name']} and keep the rest of the look simple.")
            else:
                suggestions.append(f"Use {item_name} as the statement layer over a basic top and jeans.")
        elif category == "shoes":
            if best_bottom and best_top:
                suggestions.append(
                    f"Step into {item_name} with {best_bottom['name']} and {best_top['name']} for a cohesive outfit."
                )
            elif best_bottom:
                suggestions.append(f"Pair {item_name} with {best_bottom['name']} and a low-key top to let the shoes stand out.")
            else:
                suggestions.append(f"Use {item_name} to anchor a simple, tonal outfit.")
        else:
            if best_top and best_bottom:
                suggestions.append(
                    f"Add {item_name} to {best_top['name']} and {best_bottom['name']} for a complete outfit with extra detail."
                )
            elif best_top:
                suggestions.append(f"Style {item_name} with {best_top['name']} and keep the rest of the look understated.")
            elif best_bottom:
                suggestions.append(f"Wear {item_name} with {best_bottom['name']} and a simple top for a clean look.")
            else:
                suggestions.append(f"Use {item_name} as the finishing touch on a relaxed, layered outfit.")

        if best_accessory and category != "accessories":
            suggestions.append(f"Finish the look with {best_accessory['name']} to tie everything together.")

        if not suggestions:
            return "I'm not sure how to style this item."

        return " ".join(suggestions)
    except Exception:
        return "I'm not sure how to style this item."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit: The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.
    """
    
    if not outfit or not outfit.strip():
        return "Outfit suggestion is missing. Please try again."

    title = new_item.get("title", "this find")
    price_text = _format_price(new_item.get("price"))
    platform = new_item.get("platform", "a resale platform")

    vibe = "vintage-inspired" if "vintage" in outfit.lower() or "vintage" in [tag.lower() for tag in new_item.get("style_tags", [])] else "effortlessly cool"
    caption = (
        f"Just scored {title} for {price_text} on {platform}. "
        f"I styled it with {outfit[0].lower() + outfit[1:] if outfit[0].isupper() else outfit} "
        f"and the whole look feels {vibe}. "
        f"Perfect for when I want a relaxed outfit with a statement piece."
    )

    return caption