# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## Tool Inventory

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
search_listings returns 3 matching listings sorted by relevance.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Description of item user is looking for
- `size` (str): Size of item user is looking for
- `max_price` (float): Maximum price user is willing to pay

**What it returns:**
It returns three matching listings sorted by result. The result contains:
- List of 3 dictionary entries matching search conditions by relevance
- The dictionary values have a key containing description and price of item, and the value contains where the item was found and its condition.

**What happens if it fails or returns nothing:**
If search_listings returns nothing, FitFindr tells the user what to try differently and stops — it does not call suggest_outfit with empty input.
If search_listings only finds one or two matches, it returns the matches and logs a message "I only found 1 entry that matched your search criteria."
or "I only found 2 entries that matched your search criteria."

---

### Tool 2: suggest_outfit

**What it does:**
suggest_outfit suggests an outfit based on the selected item and the user's current wardrobe.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The item the user is considering buying. This was the item selected from the list of dictionaries returned by search_listings.
- `wardrobe` (dict): The wardrobe dictionary with an 'items' key containing a list of wardrobe item dictionaries that the user already owns. M

**What it returns:**
A string with outfit containing suggestions with how to wear the new item with the user's existing wardrobe.

**What happens if it fails or returns nothing:**
- If the wardrobe is empty, it should offer general styling advice for the item rather than raising an exception or returning an empty string.
- If it fails for another reason, a fallback error message should display a message like "I'm not sure how to style this item." It then stops running - it does not suggest_outfit with empty input.

---

### Tool 3: create_fit_card

**What it does:**
create_fit_card creates a caption(fit_card) with the selected outfit, suitable for Instagram or X.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...):  The outfit suggestion string from suggest_outfit().
- `new_item`: The listing dict for the thrifted item.

**What it returns:**
- `caption`: A 2–4 sentence string usable as an Instagram/TikTok caption.
The caption should: 
    - Feel casual and authentic (like a real outfit of the day post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

**What happens if it fails or returns nothing:**
- If outfit is empty or missing, return a descriptive error message string like "Outfit suggestion is missing. Please try again." Do not raise an exception.
- If create_fit_card fails for another reason, it should display a message like "I was unable to create a caption for this outfit." It then stops running - it does not call LLM with empty input.

**What create_fit_card should do:**
1. Guard against an empty or whitespace-only outfit string.
2. Build a prompt that gives the LLM the item details and the outfit, and asks for a caption matching the style guidelines above.
3. Call the LLM and return the response.


---

## Planning Loop

**How does your agent decide which tool to call next?**
search_listings will only call suggest_outfit if a listing (or 2, or 3 listings) are returned. If not, it sends a message to the user to try a different query. If suggest_outfit fails, - If it fails fo, a fallback error message will display a message like "I'm not sure how to style this item." It then stops running - it does not suggest_outfit with empty input, and it will not cal create_fit_card.
If create_fit_card fails, it should display a message like "I was unable to create a caption for this outfit." It then stops running - it does not call LLM with empty input.


## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent stores and accesses state by assinging state and passing it to other functions. For example,  session["fit-card"] calls create_fit_card with session["outfit_suggestion"] and  session["selected_item"]. Data that is tracked includes the user's query and wardrobe, "parsed", session["search_results"], top_result = session["search_results"][0], session["outfit_suggestion"] , and session["fit_card"]. 

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool            | Failure mode                          | Agent response                                                                                                                                                                 | 
|-----------------|---------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| search_listings | No results match the query            | FitFindr tells the user what to try differently and stops — it does not call suggest_outfit with empty input.                                                                  |
| suggest_outfit  | Wardrobe is empty                     | It should offer general styling advice for the item rather than raising an exception or returning an empty string. If it fails for another reason, it stops.                   |
| create_fit_card | Outfit input is missing or incomplete | It should return a descriptive error message string like "Outfit suggestion is missing. Please try again." Do not raise an exception. If it fails for another reason, it stops.|

---

## Spec Reflection
The spec was a great starting point, and I didn't diverge from it much. The only thing that changed was that after implementation, I was getting back a full result listing instead of a dictionary with (key: description and price, value: platform and condition). So I had to make some modifications to get the correct output. 

---

## AI Usage
1. I used AI to correct syntax errors that were accidentally introduced. I pasted the errors from the console into Claude or Copilot chat (I used both), and the AI tool fixed it for me. 
2. I used AI to immplement the tool functions, testing for correct output in each case. 