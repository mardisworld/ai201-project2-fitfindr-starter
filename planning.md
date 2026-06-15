# FitFindr — planning.md

---

## Tools

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

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent stores and accesses state by assinging state and passing it to other functions. For example,  session["fit-card"] calls create_fit_card with session["outfit_suggestion"] and  session["selected_item"]. Data that is tracked includes the user's query and wardrobe, "parsed", session["search_results"], top_result = session["search_results"][0], session["outfit_suggestion"] , and session["fit_card"]. 


session["fit_card"] = create_fit_card(
        session["outfit_suggestion"],
        session["selected_item"],
    )
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response
|---------------------|--------------------------------------------------------------------------------|
| search_listings. | No results match the query | FitFindr tells the user what to try differently and stops — it does not call suggest_outfit with empty input. |
| suggest_outfit | Wardrobe is empty | It should offer general styling advice for the item rather than raising an exception or returning an empty string. If it fails for another reason, it stops. |
| create_fit_card | Outfit input is missing or incomplete | It should return a descriptive error message string like "Outfit suggestion is missing. Please try again." Do not raise an exception. If it fails for another reason, it stops. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
User input → Planning Loop → Tools (search_listings, suggest_outfit, 
create_fit_card)
↕
                                                                State / 
Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram 
(https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking 
it to implement
     the planning loop and each individual tool. -->

---

![alt text](<FitFindr Flow Diagram.png>)


## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your 
agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

### Tool 1: search_listings
I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement search_listings() using load_listings() from the data loader — then test it against 3 queries before trusting it.

### Tool 2: suggest_outfit
I'll give Claude my Tool 2 spec (inputs, return value, failure mode) and ask it to implement suggest_outfit() using load_wardrobe_schema() / get_example_wardrobe() / et_empty_wardrobe() -> dict: from the data loader. I will then test it against 3 new items before trusting it.

### Tool 3: create_fit_card

I'll give Claude my Tool 3 spec (inputs, return value, failure mode) and ask it to implement create_fit_card() using the LLM. I will then test it against 3 new outfits before trusting it.


**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**  Call `run_agent`: Main agent entry point.  session = run_agent(query=user_query, wardrobe=wardrobe): line 55 in app.py. Runs the FitFindr planning loop for a single user interaction and returns the completed session dict.(overall flow loop). Initialize the session with _new_session(). session = _new_session(query, wardrobe) - line 106 in agent.py

**Step 2:** Parse the user's query to extract a description, size, and max_price. 

session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price,
        "max_price_formatted": _format_price(max_price),
    } - lines 125 - 130 in agent.py

**Step 3:** Call search_listings() with the parsed parameters. Store results in session["search_results"]. If no results: set session["error"] to a helpful message and return the session early. Do NOT proceed to suggest_outfit with empty input.

session["search_results"] = search_listings(
        description=description,
        size=size,
        max_price=max_price,
    ) - lines 132 - 136 in agent.py

**Step 4:** In search_listings() function, select the item to use (e.g., the top result). Store it in session["selected_item"].

 session["selected_item"] = next(
    (l for l in all_listings if l.get("description", "").strip() in top_description),
    top_result,
    ) - lines 149-152 in agent.py 

**Step 5:** Call suggest_outfit() with the selected item and wardrobe. Store the result in session["outfit_suggestion"].

   session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"],
        wardrobe,
    ) - lines 154-157 in agent.py 

**Step 6:** Call create_fit_card() with the outfit suggestion and selected item. Store the result in session["fit_card"].

    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"],
        session["selected_item"],
    ) - lines 158-161 in agent.py 

**Step 7:** Return the session.

  return session - line 163 in agent.py


**Final output to user:**
fit_card/caption