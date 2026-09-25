# English Pattern Catalog

Sources: tier system distilled from conorbronsdon/avoid-ai-writing (which credits brandonwise/humanizer's vocabulary research), pattern groups from blader/humanizer v3, watch lists from Wikipedia's *Signs of AI writing*, structural regexes adapted from sam-paech/antislop-sampler. Every Before/After pair below either comes from those sources or is exercised in `scripts/test_slop_check.py`.

**Why AI text sounds like this** (blader's account, worth internalizing before editing): an LLM writes whatever is most likely to come next, so by default it makes the choice that fits the widest range of readers and subjects. A person chooses for one reader and one subject. Every tell below is a form of that default choice: signaling importance instead of adding a fact, rhythm applied by rule, an ordinary fact dressed as a pivotal one, or text left over from the chat.

**Portability test**: if a sentence could move unchanged to another person, company, country, or product, it is filler. Cut it or replace it with a fact, example, mechanism, or judgment specific to this subject.

---

## A. Vocabulary tiers

**Authority note**: the runnable lexicon is `scripts/data/en.json`; the word lists below are
presentation (replace-hints), not the source of truth. When they disagree, JSON wins — fix this file.

### Tier 1A — AI frequency markers (review every match)

Strongest evidence about how a passage was produced. Carve-outs: literal and technical uses are protected (`robust` in engineering, `landscape` in geography, `ecosystem` in biology).

| Replace | With |
|---|---|
| delve / delving into | explore, dig into, look at |
| tapestry | describe the actual complexity |
| testament to | shows, proves, demonstrates |
| realm | area, field, domain |
| paradigm (shift) | model, approach, or name the shift |
| pivotal, crucial | important, key, necessary |
| leverage (verb) | use |
| seamless(ly) | smooth, easy, without friction |
| meticulous(ly) | careful, detailed, precise |
| game-changer | say what specifically changed and why it matters |
| nestled | is located, sits, is in |
| vibrant, thriving | describe what makes it active, or cite a number |
| showcasing | showing, or cut the clause |
| cutting-edge | latest, newest, advanced |
| ever-evolving | changing, growing, or describe how |
| at its core | cut — just state the thing |
| synergy | describe the actual combined effect |
| plays a crucial/vital role | say what it actually does |
| commendable | say what was actually good (Liang 2024: 9.8x in ICLR reviews) |
| garnered | won, earned, got |
| unveiled | announced, released, showed |
| invaluable / noteworthy / versatile | helped how? name the outcome or use cases |
| skyrocketing | give the number |
| aptly / lucidly / comprehensively | cut the adverb, or show the coverage |

Before → After (Wikipedia examples, condensed):

- ❌ The temple underscores its role in bringing together Latter-day Saints from the United States and Mexico.
- ✅ State who uses the temple and what it hosts.

### Tier 1B — clarity edits (wordiness, not authorship evidence)

Replacing them is good writing regardless of who wrote the sentence. The detector reports them but **excludes them from the AI-evidence score**, so a wordiness fix can never push a document toward an AI classification: utilize→use, in order to→to, due to the fact that→because, serves as→is, boasts→has, commence→start, ascertain→find out. Copula-avoidance family (Geng & Trotta via WP:AISIGNS — LLMs drop plain is/are/has ~10% more often): represents a→is, marks a→is, features a→has, offers a glimpse→shows.

### Tier 2 — flag when 2+ distinct entries appear in the same paragraph

Individually fine; together they are a strong AI signal: harness, navigate, foster, elevate, unleash, streamline, empower, bolster, spearhead, resonate with, revolutionize, facilitate, underpin, nuanced, multifaceted, myriad, plethora, encompass, catalyze, reimagine, transformative, cornerstone, paramount, poised to, burgeoning, nascent, quintessential, overarching, groundbreaking, renowned, vital.

### Tier 3 — flag only at high density

Normal words AI uses instead of specifics. Suppressed until saturated, then replace some with numbers, comparisons, examples: significant(ly), innovative/innovation, effective(ly), dynamic, scalable, compelling, unprecedented, exceptional(ly), remarkable(ly), sophisticated, instrumental, world-class / state-of-the-art / best-in-class; v1.1 adds enhance(d/ments), insights, findings, exhibited, align with (anti-ai-tell density_watch: Kobak common-set markers).

## B. Staging instead of stating

1. **Not X but Y** — "It's not just X, it's Y", "This doesn't mean X. It means Y.", and the split-sentence form ("The headline isn't the speed. The real story is Y.") all count. State the point directly.
   - ❌ Lisbon isn't just a place to visit — it's a place to fall in love with.
   - ✅ I would go back, but in spring and with better shoes.
2. **One-line closers and dramatic fragments** — "That is the real win." after every section; "No prior. No nostalgia." Merge fragments into a specific claim, or cut.
3. **Sayings that sound deep** — "At its core, what matters is…", "X is the language of Y." Replace the aphorism with the specific claim.
4. **Staged run-up** — "Let's dive in", "Honestly? It depends…" Remove the run-up and state the point.
5. **Arguing with no one** — "This isn't mainly about…", "A tempting approach would be…" Remove the unraised objection; keep any real claim.

## C. Rhythm by rule

6. **Forced triads** — "innovation, inspiration, and insights"; three parallel examples plus a lesson. Use the number of items the meaning needs. A genuine list of three real items stays.
7. **Repeated sentence openings** — "She noted… She noted… She filed…" Merge or change the subject.
8. **Dashes as the universal connector** *(weak alone)* — density flag at 4+ per document. Use periods, commas, colons, parentheses.
9. **Stacked qualifiers** *(weak alone)* — "could potentially possibly be argued". Keep only the qualifier the source supports.
10. **Passive voice / missing subjects** *(weak alone)* — "No configuration file needed." Name the actor when that helps; README/changelog fragments are the correct form and pass.

## D. Inflation and borrowed authority

11. **Inflated significance** — "marking a pivotal moment", "Despite challenges… continues to thrive", "The future looks bright", "the transformative power of", "left an indelible mark", "setting the stage for". Keep the fact, drop the significance; end on the last concrete fact.
12. **Superficial -ing riders** — "symbolizing… reflecting… showcasing…" Keep only what the source supports.
13. **Sales language** — "nestled within the breathtaking region", "a vibrant hub of innovation". State what the thing is.
14. **Borrowed authority** — "Experts believe…", "cited in NYT, BBC, FT" (notability name-dropping), "independent testing confirms" (vague third-party validation). Name a real source and what it said, or remove the claim. Carve-out: specifically attributed, checkable validation ("SOC 2 Type II, audited by Prescient Assurance") stays.
15. **Copula avoidance** — "serves as", "features", "boasts" for plain is/has. Default to "is".
    - ❌ The app serves as a centralized hub for sponsor management.
    - ✅ The app tracks sponsors, drafts, due dates, and approvals in one place.
15b. **Drumroll punctuation** *(weak alone)* — rhetorical self-answers ("The catch? Nobody tells you…"), label-and-explain colons ("The tradeoff:", "The bottom line:"), meta-commentary ("This matters because…", "The key here is…"), leftover bold markup ("**Key takeaway:**"). Integrate the point into the surrounding sentence; delete the label.
15c. **Journey metaphors** — "paves the way", "along the way", "the road ahead", "offers a glimpse into". Replace with the actual consequence ("enabled", "made possible"), or cut.

## E. Formatting by rule

16. **Bold as decoration**; emoji in headers; title-case subheadings in a sentence-case document; bullet lists where two sentences of prose would read better.
17. **Hashtag stuffing** — 6+ trailing tags on one post. 2–3 specific tags max, or none.

## F. Leftovers from the chat

18. **Chatbot residue** — "I hope this helps!", "Certainly!", "Great question!", "Let me know if you need anything else". Remove the wrapper, keep the content.
19. **Knowledge-limit disclaimers & speculative gap-filling** — "As of my last update…", "While details are limited…", "is believed to have…". State what the source shows, or cut. Never turn missing information into a confident claim.
20. **Summary-recap endings** — "In conclusion," "Ultimately," a final paragraph restating the piece. End on the last concrete point, takeaway, or next action.
21. **Meta-narration** — "In this article, we will explore…", "Here's what stood out", "That last part matters more than it sounds." Let the content signal its own importance.

## Worked example (from blader/humanizer, condensed)

Before (AI-sounding): *Nestled along the banks of the Tagus River, Lisbon stands as a vibrant testament to Portugal's enduring spirit, where rich history and modern energy intertwine at every turn… But what truly makes Lisbon special isn't just the sights — it's the feeling… Lisbon isn't just a place to visit — it's a place to fall in love with, again and again.*

After (human): *I spent five days in Lisbon last October and still have mixed feelings about it. Beautiful, yes. Also harder on the knees than anyone warned me… The custard tarts, though, earn the fuss. I had one at a plain little place in Graça, still warm, and for about thirty seconds I understood why people build trips around pastry.*

Both versions are in `scripts/test_slop_check.py`: the before scores `heavy`, the after scores `clean` with zero findings — that pair is the calibration target for this skill.
