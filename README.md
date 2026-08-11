<div align="center">

# <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/2708_fe0f/512.webp" alt="✈️" width="46" height="46" align="absmiddle"> AI Travel Planner

### An agentic travel planner for India that refuses to make things up.

*Eleven tools. Five dependencies. Zero frameworks.*
*One stubborn rule: if it isn't in the data, the agent says so.*

<br>

<img src="https://cdn.simpleicons.org/python/3776AB" height="42" alt="Python"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/streamlit/FF4B4B" height="42" alt="Streamlit"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/pandas/150458" height="42" alt="pandas"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/kaggle/20BEFF" height="42" alt="Kaggle"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/openstreetmap/7EBC6F" height="42" alt="OpenStreetMap"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/visualstudiocode/007ACC" height="42" alt="VS Code"/>

<br><br>

**Bring your own brain — every one of these works today**

<img src="https://cdn.simpleicons.org/googlegemini/8E75B2" height="34" alt="Gemini"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/google/4285F4" height="34" alt="Gemma"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/nvidia/76B900" height="34" alt="NVIDIA Nemotron"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/anthropic/D97757" height="34" alt="Claude"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/openai/412991" height="34" alt="OpenAI"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/meta/0866FF" height="34" alt="Llama"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/mistralai/FA520F" height="34" alt="Mistral"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/huggingface/FFD21E" height="34" alt="Hugging Face"/>&nbsp;&nbsp;
<img src="https://cdn.simpleicons.org/ollama/FFFFFF" height="34" alt="Ollama"/>

<br>

![Gemini 3.6](https://img.shields.io/badge/Gemini_3.6_Flash-8E75B2?style=flat-square)
![Gemma 4](https://img.shields.io/badge/Gemma_4-4285F4?style=flat-square)
![Nemotron 3](https://img.shields.io/badge/Nemotron_3-76B900?style=flat-square)
![DeepSeek](https://img.shields.io/badge/DeepSeek_V4-4D6BFE?style=flat-square)
![Qwen](https://img.shields.io/badge/Qwen_3-615CED?style=flat-square)
![OpenRouter](https://img.shields.io/badge/OpenRouter-400+_models-1F2937?style=flat-square)

<br>

**Live data, free forever, no keys**

![Open-Meteo](https://img.shields.io/badge/Open--Meteo-weather-0EA5E9?style=for-the-badge)
![Nominatim](https://img.shields.io/badge/Nominatim-places-7EBC6F?style=for-the-badge)
![Frankfurter](https://img.shields.io/badge/Frankfurter-currency-F59E0B?style=for-the-badge)

</div>

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f3ac/512.webp" alt="🎬" width="30" height="30" align="absmiddle"> So what does it actually do?

You type *"plan me five days in Jaipur, mid-range, two of us."*

The agent doesn't answer straight away, because it doesn't know enough yet. It goes and looks. It checks whether Jaipur is even in your datasets. It pulls real attractions with their real entrance fees. It fetches the actual weather forecast, spots that Thursday is 90% rain, and quietly moves the fort to Friday and the museum to Thursday. It prices hotels from genuine listings instead of vibes. Then it writes the plan up and offers to email you a PDF.

Now ask it about a city your data doesn't cover.

It tells you it doesn't know.

No charming boutique hotel that has never existed. No entrance fee it made up because a number felt owed. Just an honest *"I don't have data for that — want me to try the live sources instead, clearly labelled?"*

That refusal is the product. Everything else is plumbing.

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f914/512.webp" alt="🤔" width="30" height="30" align="absmiddle"> Why bother building this?

Most "AI travel planner" projects are one API call wearing a trenchcoat. A prompt goes to a model, prose comes back, and the model cheerfully invents hotel names, entrance fees, and a restaurant that closed in 2019. It looks impressive for exactly as long as nobody checks.

The industry noticed. As one 2026 travel-tech retrospective put it, the chatbot era gave us assistants that could write a poem about Paris but couldn't book a hotel room without hallucinating the address. That's the bar this project is trying to clear — not eloquence, *correctness*.

And it was built under a constraint that turned out to be a gift:

> **You get five libraries. `streamlit`, `google-genai`, `requests`, `reportlab`, `pandas`. That's the whole budget.**

No LangChain. No ChromaDB. No vector store. No agent framework of any kind.

So the agent loop, the tool registry, the retrieval engine, the provider abstraction — all of it is written out by hand, in roughly 800 lines you can sit down and read in an afternoon. Nothing hides behind a decorator that quietly does six things.

That's not a limitation. That's the syllabus.

<div align="center">

*"I could have imported an agent framework. Instead I found out what one does."*

</div>

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/26a1/512.webp" alt="⚡" width="30" height="30" align="absmiddle"> Getting it running

Six steps. Ten minutes, most of which is Kaggle.

### 1️⃣ Grab the datasets

Free Kaggle account, three downloads:

| Dataset | What you get | Link |
|:--|:--|:--|
| 🏛️ **India's Must-See Places** | Attractions, ratings, entry fees, best season | [`saketk511/travel-dataset-guide-to-indias-must-see-places`](https://www.kaggle.com/datasets/saketk511/travel-dataset-guide-to-indias-must-see-places) |
| 🏨 **Hotels on Goibibo** | Real listings, prices, amenities, reviews | [`PromptCloudHQ/hotels-on-goibibo`](https://www.kaggle.com/datasets/PromptCloudHQ/hotels-on-goibibo) |
| 🗺️ **Indian Tourism Itinerary** | Day-wise reference plans worth adapting | [`vaibhavanuragi2004/indian-tourism-itinerary`](https://www.kaggle.com/datasets/vaibhavanuragi2004/indian-tourism-itinerary) |

### 2️⃣ Make the folder, drop the CSVs in

```bash
mkdir -p data/cleaned
```

Unzip the downloads and put the CSV files in `data/cleaned/`. **Don't rename anything.** Seriously. The app identifies files by reading their column headers, not their names, and it's rather good at it.

```
data/cleaned/
├── Cleaned_Tourist_Guide.csv
├── Cleaned_Hotel_Info.csv
├── Cleaned_Iternary_Dataset.csv          ← typo and all, it copes
├── Worldwide_Travel_Cities_Cleaned.csv
└── travel_details_cleaned.csv
```

### 3️⃣ Open it in VS Code

```bash
cd "path/to/travel-planner-agent"
code .
```

Terminal: **`Ctrl` + `` ` ``** (that's the backtick, top-left of your keyboard), or **View → Terminal**.

### 4️⃣ Virtual environment

```bash
python -m venv .venv
```

Then activate it — pick your shell:

```powershell
.venv\Scripts\Activate.ps1      # Windows PowerShell
```
```cmd
.venv\Scripts\activate.bat      # Windows CMD
```
```bash
source .venv/bin/activate       # macOS / Linux
```

Your prompt should now begin with `(.venv)`. If PowerShell throws an execution-policy tantrum, this fixes it permanently:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

> 💡 **The lazy way:** `Ctrl+Shift+P` → *Python: Create Environment* → *Venv* → tick `requirements.txt`. VS Code does steps 4 and 5 together and points the interpreter at the right place, which saves you the classic *"but I installed it!"* half hour.

### 5️⃣ Install

```bash
pip install -r requirements.txt
```

Five packages. Under a minute.

### 6️⃣ Go

```bash
streamlit run app.py
```

Browser opens at `http://localhost:8501`. Paste an API key into the sidebar's **API keys** panel, hit **Test**, and you're planning trips. <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f389/512.webp" alt="🎉" width="24" height="24" align="absmiddle">

<details>
<summary><b>🔍 Worth doing first: check your data before you check your key</b></summary>

<br>

```bash
python smoke_test.py
```

Loads every dataset, resolves every column, pings every live API — **without touching an LLM.** If something's wrong with your CSVs you find out now, in one readable table, instead of twenty minutes later as a mysteriously empty answer that you'll blame on the model.

```bash
python smoke_test.py --llm
```

Also lists every model your keys can reach and round-trips the default one. Needs keys in `.env` — the sidebar ones live in the browser session only.

</details>

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f511/512.webp" alt="🔑" width="30" height="30" align="absmiddle"> Two keys. Both free. One is enough.

| Key | What it unlocks | Get it |
|:--|:--|:--|
| `GOOGLE_API_KEY` | **Every** Gemini and Gemma model | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `OPENROUTER_API_KEY` | **Every** model on OpenRouter — Claude, GPT, DeepSeek, Llama, Qwen, Mistral, Nemotron… | [openrouter.ai/keys](https://openrouter.ai/keys) |

Paste into the sidebar (session-only, never written to disk), or put them in a `.env` next to `app.py` if you'd like them to stick around:

```bash
GOOGLE_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...
```

Email needs **no key at all** on the default route — see below.

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f4e7/512.webp" alt="📧" width="30" height="30" align="absmiddle"> Emailing the itinerary — three routes, pick your pain level

There is one honest constraint here and it's worth stating plainly: **nothing can send
email as you without proving you're allowed to.** That's not a design flaw, it's the only
thing standing between the internet and infinite spam. Every option below is a different
answer to "how do I prove it?"

The good news: the default route needs no proof at all, because *you* send it.

| Route | Setup | How it feels |
|:--|:--|:--|
| 🟢 **Send it yourself** | **None** | Download the PDF, click *Open in Gmail*, drag it in, send. ~15 seconds. |
| ⚡ **Resend** | One API key | Paste a key, get one-click send with the PDF attached. |
| 📮 **Gmail SMTP** | App password + 2FA | Fiddliest, but sends from your own address forever. |

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f7e2/512.webp" alt="🟢" width="25" height="25" align="absmiddle"> Route 1 — Send it yourself (the default, zero setup)

Open the **📄 Export** tab. This is what you see immediately, no configuration needed:

```
Send to:  friend@example.com

[ 1 · Download PDF ]     [ 2 · Open in Gmail → ]
```

Click **1**, click **2**. Gmail opens in a new tab with the recipient, subject and a full
day-by-day message already written. Drag the PDF into the compose window and hit send.

It arrives from *your* Gmail, which means it looks like a normal email from a human and
never gets filtered as spam. Honestly, for a demo or a one-off, this is the right answer
and you can stop reading here.

Outlook, Yahoo and your desktop mail client are behind **Other mail apps**.

> ⚠️ The desktop `mailto:` option hands off to whatever your OS registered as the default
> mail handler. If that's nothing — common on Windows — you get a "how do you want to open
> this?" dialog and nothing useful. Use the Gmail button instead.

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/26a1/512.webp" alt="⚡" width="25" height="25" align="absmiddle"> Route 2 — Resend (one key, genuinely easy)

Want the **Send** button to just work, PDF attached, no dragging? This is the least
painful way to get there.

1. Sign up at **[resend.com](https://resend.com)** with GitHub or Google
2. Copy the API key it shows you — starts with `re_`
3. Export tab → **⚙️ connect an account** → **⚡ Resend** tab → paste → done

That's it. One field, no 2-factor dance, no SMTP settings, no app passwords.

> 📌 **The one catch, stated up front:** free Resend accounts send from
> `onboarding@resend.dev` and can **only mail the address you signed up with**, until you
> verify a domain. Perfect for testing and demos. If you need to mail anyone, add a domain
> at [resend.com/domains](https://resend.com/domains) — a few minutes of DNS records.

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f4ee/512.webp" alt="📮" width="25" height="25" align="absmiddle"> Route 3 — Gmail SMTP (most setup, best result)

Sends from your real Gmail address, permanently, to anyone. Worth doing if this app
becomes something you actually use. Here's the part that confuses everyone:

> ### An App Password is **not** a password you invent.
> Google **generates** a 16-letter password for you — a disposable credential for one app,
> so your real password never touches a program. It's displayed as four groups of four,
> like `abcd efgh ijkl mnop`.
>
> Type your normal Gmail password in and Google **will** reject it. Always. Even though
> it's correct. That's the `535 5.7.8 BadCredentials` error.

**Step 1 — Turn on 2-Step Verification.**
👉 **https://myaccount.google.com/security** → **2-Step Verification** → on.

Not optional: **the app-password page does not exist until 2FA is enabled.** Go looking
for it first and Google silently redirects you, and you'll assume the link is broken.

> 💾 While you're there, download your **backup codes**. If you lose your phone, those are
> how you get back in. Recovering a 2FA-protected Google account without them is grim.

**Step 2 — Generate the password.**
👉 **https://myaccount.google.com/apppasswords**

Note the **`myaccount.`** prefix — plain `google.com/apppasswords` is not a real page.

Type any app name (`Travel Planner` is fine — it's just a label for revoking later), click
**Create**, and Google shows 16 letters in a yellow box. **Copy them now** — it's shown
exactly once. Lost it? Delete the entry and make another; it costs thirty seconds.

<details>
<summary>The page redirects me / says it isn't available</summary>

<br>

1. **2FA isn't fully enabled.** Finish step 1 — Google leaves it half-done if you close the tab early.
2. **Wrong account.** Check the avatar top-right. A college account signed in elsewhere can hijack the link.
3. **Admin has disabled app passwords.** Common on college and Workspace accounts, nothing you can do. Use Route 1 or 2.

</details>

**Step 3 — Paste it in.** Export tab → **📮 Gmail** tab → **App password**.

Paste it exactly as Google showed it — **spaces and all**, the app strips them. Pasting
beats retyping; dropping one letter is the number one cause of failure. Watch the chip:

| Chip | Meaning |
|:--|:--|
| 🟢 `16 characters ✓` | Good. |
| 🟡 `14 characters — app passwords are exactly 16` | Paste got clipped. Copy again. |
| 🟡 `app passwords are letters only` | That isn't an app password. |

**Step 4 — Hit Send test email.** It mails you, so check your own inbox.

<details>
<summary>Still getting <code>535 Username and Password not accepted</code></summary>

<br>

The app prints Google's own response so you can tell the causes apart:

| Google says | Meaning |
|:--|:--|
| `534 Application-specific password required` | You used your account password. |
| `535 5.7.8 BadCredentials` | Wrong or revoked app password — **or** the Gmail address doesn't match the account that generated it. |
| Anything about *disabled* | SMTP or app passwords blocked by admin policy. |

Stubborn `535`: delete the app password in Google, generate a fresh one, paste again.
Sometimes the first copy just goes wrong.

</details>

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f512/512.webp" alt="🔒" width="25" height="25" align="absmiddle"> Revoking access

**Resend:** [resend.com/api-keys](https://resend.com/api-keys) → delete the key.
**Gmail:** [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) → 🗑️ next to the entry.

Both take effect instantly. Worth doing before pushing to a public repo or recording a
demo where the Export tab is on screen. Regenerating takes under a minute — disposable is
the entire point.

Credentials pasted into the sidebar live in the browser session only and are never written
to disk. `.env` is gitignored. The realistic leak path is a screenshot, not the code.

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f9f9/512.webp" alt="🧹" width="30" height="30" align="absmiddle"> A word about "cleaned"

These datasets are good. They are not clean. Nobody's are. Here's the honest split between what the app absorbs for you and what's still your job.

### What it handles on its own 🤖

**Column-name chaos.** `Google review rating`, `google_review_rating`, `rating`, `site_review_rating` all land on the same logical column, via a normaliser plus a synonym table. You'll probably never open the mapping file.

**Encoding roulette.** UTF-8, then UTF-8-BOM, then Latin-1. Indian place names carry diacritics that make a naive `read_csv` fall over sideways.

**Numbers pretending to be strings.** `"₹200"`, `"200 INR"`, `"Free"`, `NaN`. All parsed defensively, and anything unparseable gets dropped from calculations rather than quietly poisoning them.

**Filename anarchy.** Files are scored against dataset slots by their headers. `Cleaned_Iternary_Dataset.csv` lands in the itinerary slot despite the spelling, because the columns give the game away.

### What's still on you 🧑‍🔧

**Duplicates.** The Goibibo dump repeats itself. Deduplicate on property name + city, or your price quantiles drift toward whatever got scraped twice.

**Price outliers.** Some listings are ₹50. Some are ₹8,00,000. The budget tool clips to a sane band, but trimming the top and bottom percentile first noticeably improves the estimates.

**City name variants.** Bangalore vs Bengaluru. Goa vs Panaji vs North Goa. The app normalises case and punctuation, but it can't know those are the same place. **Pick one spelling per city.** This single step improves coverage more than everything else on this list combined.

**Empty descriptions.** Rows with no free text are invisible to lexical ranking. They'll still match hard filters, but they'll never surface for *"peaceful temple with a garden."*

**The sneaky header row.** Sounds obvious. Isn't. A CSV exported from Excel sometimes carries a title row above the real headers, and every column becomes `Unnamed: 0`. The uploader catches this and tells you, but check anyway.

> 🧭 **Straight talk:** hand this app a lightly-cleaned Kaggle dump and it works. Every extra hour you put into the data makes the agent measurably better. The ceiling here isn't the model. It's the rows.

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f3d7_fe0f/512.webp" alt="🏗️" width="30" height="30" align="absmiddle"> How it actually works

Four layers, and each one does exactly one job. Follow a single question through them and the whole system makes sense.

```
   YOU ─── "5 days in Jaipur, mid-range, 2 people"
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  🖥️  PRESENTATION            app.py · ui/                      │
│      Chat · Itinerary · Budget · Export · Dataset manager      │
│      Owns nothing. Renders what the layers below produce.      │
└───────────────────────────┬───────────────────────────────────┘
                            │  neutral message list
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  🧠  ORCHESTRATION           agent/loop.py                      │
│      for step in 1..6:                                         │
│          reply = provider.chat(messages, tool_schemas)         │
│          if not reply.tool_calls:  →  done, return the answer  │
│          run each tool, append results, go round again         │
│                                                                │
│      Knows nothing about Gemini, or CSVs, or the weather.      │
│      Just: ask, execute, feed back, repeat, stop.              │
└──────────┬────────────────────────────────────┬───────────────┘
           │                                    │
           ▼                                    ▼
┌────────────────────────────┐   ┌──────────────────────────────┐
│  🔌  MODEL ACCESS           │   │  🛠️  CAPABILITY               │
│      providers/            │   │      tools/ · registry.py     │
│                            │   │                               │
│  Google SDK ──┐            │   │  11 plain Python functions,   │
│               ├─► Reply    │   │  each with a JSON schema the  │
│  requests ────┘            │   │  model reads as documentation │
│                            │   │                               │
│  Two wire formats.         │   │  🗄️ INSIDE      🌍 OUTSIDE     │
│  One neutral object.       │   │  your CSVs      live APIs     │
│  400+ models behind it.    │   │  ─────────      ─────────     │
│                            │   │  coverage       weather       │
│  Gemini · Gemma            │   │  attractions    places        │
│  Claude · GPT · DeepSeek   │   │  hotels         currency      │
│  Llama · Qwen · Mistral    │   │  itineraries    email         │
│  Nemotron · and the rest   │   │  + budget · plan · PDF        │
└────────────────────────────┘   └───────────────┬───────────────┘
                                                 │
                                                 ▼
                                 ┌───────────────────────────────┐
                                 │  🗄️  KNOWLEDGE                 │
                                 │      data_layer/               │
                                 │                                │
                                 │  discovery → which file is     │
                                 │              which dataset?    │
                                 │  schema    → which column is   │
                                 │              which field?      │
                                 │  retrieval → filter, then rank │
                                 └───────────────────────────────┘
```

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f501/512.webp" alt="🔁" width="25" height="25" align="absmiddle"> One question, start to finish

Here's what happens between you pressing Enter and the plan appearing. This is a real trace, not a diagram of one.

**Step 1.** The loop sends your message plus eleven tool descriptions to whichever model you picked. The model reads the system prompt — which says, in short, *ground everything or admit you can't* — and replies: `check_city_coverage(city="Jaipur")`.

**Step 2.** The loop runs it. The data layer filters four datasets and reports back: 3 destinations, 30 hotels, 1 itinerary, 1 city row. Verdict: covered. That string is pasted into the conversation and the loop goes round again.

**Step 3.** Now confident, the model fires off several tools at once: `search_destinations`, `get_weather_forecast`, `estimate_budget`. They run, they return, the results go back in.

**Step 4.** The model calls `build_itinerary`. Behind the scenes this one is doing real work — pulling the top attractions, fetching the forecast day by day, sorting places into indoor and outdoor, and putting the museums on the 90%-rain day. It writes the structured plan into shared state, which is how the **Itinerary** tab suddenly has something to show.

**Step 5.** No more tool calls. The model writes the answer in markdown. The loop returns it, the chat renders it, and the **Agent Trace** expander below the reply lists every call that got you there.

Five model round-trips. Four tools. Zero invented hotels.

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f6a7/512.webp" alt="🚧" width="25" height="25" align="absmiddle"> The three rules that make a loop into an agent

Writing the loop is easy. Making it survive contact with reality is where the work is.

**A broken tool must never break the loop.** Every failure becomes a readable sentence the model can reason about — *"Tool 'search_hotels' failed: connection timeout."* The model then apologises to you, works around it, and carries on. Compare that to a stack trace ending your conversation.

**Bad arguments are a teaching moment, not a crash.** Call a tool with the wrong parameter and you get told what the schema expected, so you can try again. Models do this more than you'd think, and recovering gracefully is most of the difference between a demo and a tool.

**The step budget is a wall, not a suggestion.** Six iterations, then it stops and says so. An agent that *can* loop forever eventually will, usually while you're presenting it.

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f50d/512.webp" alt="🔍" width="25" height="25" align="absmiddle"> Retrieval, and why there's no vector database

The original spec called for ChromaDB and embeddings. Then somebody asked *why*, and there wasn't a good answer.

Semantic search exists for when you don't know the shape of your data. But we know the shape precisely — there's a `city` column, right there. Using cosine similarity to find rows where city equals "Jaipur" is an elaborate way of avoiding `==`.

So retrieval is two honest stages:

**Stage 1 — hard filter.** Deterministic pandas filtering on city, state, type, price band. Ten thousand rows become forty. Exact, instant, free.

**Stage 2 — lexical rank.** Only if there's a free-text query, and only over what survived stage 1. A hand-written IDF scorer weights rare words heavily and common ones barely, then divides by length so a rambling description can't win on sheer volume.

```
score = Σ log(N / (1 + df[token]))  ÷  √(row length)
```

That's the entire ranking function. Fifteen lines. No embedding call per query, no index to rebuild, no 400 MB dependency — and you can explain it out loud without waving your hands.

> 🎓 **How to defend it in a viva:** *"Vector search is for unknown schemas. I know mine, so I filter on it and fall back to lexical matching only for free-text columns. Cheaper, deterministic, and there's no embedding cost per query."*

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f50c/512.webp" alt="🔌" width="25" height="25" align="absmiddle"> Two wire formats, every model on Earth

Hundreds of models, four vendors, and only **two** ways of speaking:

| Backend | Transport | Reaches |
|:--|:--|:--|
| Google AI Studio | `google-genai` SDK | Gemini + Gemma — one client, the model string is the only difference |
| OpenRouter | plain `requests` | Everything else, OpenAI-compatible |

Every provider normalises down to one `Reply` object. The agent loop genuinely does not know which model it's talking to.

That indifference is why this project is still standing. During the build, NVIDIA's org policy locked the account, Hugging Face turned out to have nobody hosting the model, Gemini 2.5 was retired for new users mid-project, and Gemini 3 broke on an undocumented requirement. Four vendor failures. Adding OpenRouter as an escape route cost **one dictionary entry**.

Model IDs are never hardcoded, because that's precisely what kept breaking. The app asks each backend what it serves *right now*, hides models without tool-calling support (a model that can't call your tools will chat delightfully and invent hotels), and sorts newest-first by parsing version numbers out of the slugs.

<details>
<summary><b>🐛 Two bugs that cost an evening each, now three lines and a comment</b></summary>

<br>

**Gemini 3.5+ removed the sampling parameters.** Sending `temperature` is now an error rather than a preference. Handled with a per-model capability flag.

**Gemini 3 requires `thought_signature` echoed back.** Every function-call part carries an opaque signature that has to return unchanged on the following turn. Rebuilding the assistant message from your own objects silently drops it — so turn one works, turn two fails with a 400 that explains nothing. Fixed by replaying Gemini's own `Content` object verbatim instead of reconstructing it.

Neither is in a tutorial. Both are in the code now, with comments explaining why, so the next person loses zero evenings.

</details>

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f9f0/512.webp" alt="🧰" width="30" height="30" align="absmiddle"> The eleven tools

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f5c4_fe0f/512.webp" alt="🗄️" width="25" height="25" align="absmiddle"> Inside — your data

| Tool | What it does |
|:--|:--|
| `check_city_coverage` | Asks the honest question first: do we have *any* rows for this city? This one tool eliminates the entire category of confident-fiction failures. |
| `search_destinations` | Attractions with ratings, entry fees, best season, hours needed. |
| `search_hotels` | Real listings by city and price tier — where the tiers are **computed from actual price quantiles**, not conjured. |
| `get_reference_itinerary` | Existing day-wise plans, used as a skeleton to adapt rather than inventing from a blank page. |

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f30d/512.webp" alt="🌍" width="25" height="25" align="absmiddle"> Outside — live, free, keyless

| Tool | Source |
|:--|:--|
| `get_weather_forecast` | Open-Meteo. Geocode, then a 16-day daily forecast with rain probability. |
| `search_places` | OpenStreetMap Nominatim, with the required User-Agent and a self-enforced 1 request/second limit. Volunteers run that service — please leave the rate limiter alone. |
| `convert_currency` | Frankfurter. INR base, live rates. |

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f9ee/512.webp" alt="🧮" width="25" height="25" align="absmiddle"> Compute and deliver

| Tool | Notes |
|:--|:--|
| `estimate_budget` | Accommodation, food, transport, activities, 10% buffer. Accommodation comes from **real hotel prices for that city**, and when it can't, the output says so instead of pretending. |
| `build_itinerary` | Attractions + forecast + reference plans. **Moves indoor sites onto the rainy days by itself.** |
| `export_itinerary_pdf` | ReportLab's Platypus layer — real text wrapping, styled tables, page numbers. |
| `send_itinerary_email` | Gmail SMTP through the standard library. Zero extra dependencies. |

Every network tool has a timeout, a `try/except`, and a graceful failure string. None of them can take the agent down with it.

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f3a8/512.webp" alt="🎨" width="30" height="30" align="absmiddle"> What you get in the browser

**💬 Chat Planner** — the conversation, with an **Agent Trace** expander underneath every reply showing each tool call, its arguments, and its raw result. This is the panel that proves the thing is real. Open it in a demo *before* anyone asks.

**🗓️ Itinerary** — expandable day cards with weather badges and cost chips. Morning, afternoon, evening, plus a note when the plan shifted indoors because of rain.

**💰 Budget** — metrics, bar chart, table, and one line stating exactly where the accommodation figure came from: *"real prices from 30 hotels in Goa (dataset quantiles)."* A number without provenance is just a rumour.

**📄 Export** — PDF download, and an email panel that does everything in-app: connect Gmail, compose to several recipients, preview, send. App passwords with spaces get stripped automatically, because Google shows them in groups of four and pasting them verbatim fails in a way that tells you nothing useful. No Gmail? There's a `mailto:` fallback that opens your own client with everything prefilled.

**🗂️ Datasets** — three ways in (**Folder**, **Upload**, **URL/Drive**, including Drive share links and the confirm-token dance for files over 100 MB), a **Mapping** tab to override which file feeds which slot, and a **Dataset Doctor** showing exactly which columns resolved and which didn't.

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f4c1/512.webp" alt="📁" width="30" height="30" align="absmiddle"> Repository structure

```
travel-planner-agent/
│
├── 📱 app.py                      Streamlit entrypoint — tabs, chat, export
├── ⚙️ config.py                   Backends, keys, constants, model quirks
├── 🧪 smoke_test.py               Test data + tools + models, no UI needed
├── 📋 requirements.txt            Five lines. That's the flex.
│
├── 🔌 providers/                  "Talk to any model"
│   ├── base.py                    Neutral Reply / ToolCall + message shapes
│   ├── google_provider.py         Gemini and Gemma, one class for both
│   ├── openai_compat_provider.py  OpenRouter, and anything OpenAI-shaped
│   ├── catalog.py                 Live model discovery — nothing hardcoded
│   └── factory.py                 backend + model → Provider
│
├── 🧠 agent/                      "Decide what to do"
│   ├── loop.py                    The executor. ~60 lines of real logic.
│   ├── registry.py                name → (schema, callable)
│   └── prompts.py                 The system prompt and its red lines
│
├── 🗄️ data_layer/                 "Know things"
│   ├── schema.py                  Every column name lives here, only here
│   ├── discovery.py               Filename-agnostic file → slot matching
│   ├── loaders.py                 Cached loading + health report
│   ├── retrieval.py               Hard filter → IDF rank → serialise
│   └── sources.py                 Upload / URL / Drive ingestion
│
├── 🛠️ tools/                      "Do things"
│   ├── dataset_tools.py           The four CSV-backed tools
│   ├── weather_tool.py            Open-Meteo
│   ├── places_tool.py             Nominatim, politely rate-limited
│   ├── currency_tool.py           Frankfurter
│   ├── budget_tool.py             Data-driven cost estimation
│   ├── itinerary_tool.py          Day composition + rain logic
│   ├── pdf_tool.py                ReportLab Platypus
│   └── email_tool.py              stdlib SMTP
│
├── 🎨 ui/                         "Look good doing it"
│   ├── theme.py                   Dark theme CSS
│   ├── components.py              Bubbles, cards, chips, trace panel
│   ├── sidebar.py                 Keys, model picker, dataset status
│   ├── data_panel.py              Upload / URL / mapping tabs
│   └── email_panel.py             In-app email, no .env needed
│
├── 🧵 utils/                      logger · helpers · shared store
│
├── 📊 data/cleaned/               Your CSVs (gitignored)
│   └── _mapping.json              Manual file → slot overrides
│
├── 📤 exports/                    Generated PDFs (gitignored)
└── 🔐 .env                        Your keys (very gitignored)
```

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1fa7a/512.webp" alt="🩺" width="30" height="30" align="absmiddle"> When it goes sideways

| What you see | What's really going on |
|:--|:--|
| *"No LLM configured yet"* | No key found. The app stops on purpose rather than failing later with something cryptic. |
| Model list says **STALE** | Couldn't reach the live catalogue, so you're looking at the offline fallback. Hit **Refresh list**. |
| `404` / `model_not_found` | Model IDs rotate constantly. Pick another from the dropdown — that's exactly why it's a dropdown. |
| `model_not_supported` | The model exists but nobody on your account serves it. Enable more providers in your OpenRouter settings. |
| `429` | Free-tier rate limit. Wait a few seconds and try again. |
| Dataset shows 🔴 | A required column didn't resolve. Open **Dataset Doctor** and fix that one entry in `schema.py`. |
| Budget says *"national averages"* | Your hotel CSV has no usable price column. Expected — and stated in the output rather than hidden. |
| The agent invents things | Check the **Agent Trace**. An empty trace means the model isn't calling tools at all. Switch models; they are not equally good at this. |
| Gmail rejects you | You used your account password. Gmail wants a 16-character **App Password**, with 2-Step Verification switched on. |

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f680/512.webp" alt="🚀" width="30" height="30" align="absmiddle"> Where this goes next

What follows isn't a wishlist. Each phase is grounded in something the 2026 industry is
actually asking for — and ordered so that each one is worth shipping on its own, even if
the next never happens.

It goes public early, at Phase 2, and deliberately not before. Open sourcing something
half-finished costs other people their afternoons.

The theme running through all of it: **2026 is the year travel AI moved from novelty to utility.** Phocuswright's research frames it as the onset of the era of autonomous agents — a shift from systems that talk to systems that *do*. IDC forecasts that by 2030, half of all AI budgets in travel and hospitality will go to personalisation. And the same reports are blunt about the blocker: fragmented data produces generic offers and broken experiences. Every phase below is a step toward the *do*, built on a foundation that can carry it.

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f9f1/512.webp" alt="🧱" width="25" height="25" align="absmiddle"> Phase 1 — Make the Streamlit build genuinely solid

**Not open source yet. Not a rewrite. Just properly finished.**

There's a temptation to jump straight to the exciting rewrite. Resisting it is the whole phase.

- A real test suite — unit tests on retrieval and budget maths, integration tests on the agent loop with a mocked provider
- Session persistence, so a browser refresh doesn't erase a plan you spent ten minutes on
- Saved trips: name it, reload it, compare two versions side by side
- Token and cost accounting displayed per conversation, because "it's free tier" stops being true the moment anyone else uses it
- Response caching for repeated tool calls within a session — the same city gets looked up three times in a typical chat
- Better empty and error states everywhere, written for someone who has never seen the app before
- A demo video and screenshots in this README, because most people decide from the pictures

**Done when:** a stranger can clone it, follow the README, and reach a working plan
without asking you a single question. That's also the bar for going public.

---
### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f331/512.webp" alt="🌱" width="25" height="25" align="absmiddle"> Phase 2 — Open it up

**Now that there's something worth cloning.**

Phase 1 made it sturdy. This makes it *shared* — and sharing it early is what turns a
portfolio piece into a project other people push forward.

- Public repository with a licence, a contribution guide, issue and PR templates, and a code of conduct
- A Docker image, so setup is one command instead of six and "works on my machine" stops being a thing
- CI on every pull request — tests, linting, and a smoke run against a mocked provider
- A hosted demo, so people can try it without cloning anything. Most will never clone; let them see it anyway
- Documentation site with the architecture written up properly, beyond this README
- Good first issues, tagged honestly, sized for someone with an afternoon
- A public roadmap the community can argue with — the arguments are the point

Open sourcing is a commitment to other people's time, not a publishing step. Doing it
*after* Phase 1 means what arrives is sturdy enough that a stranger's first hour is
spent building, not debugging your setup instructions.

**Done when:** someone you've never met opens a pull request that improves it.

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f52c/512.webp" alt="🔬" width="25" height="25" align="absmiddle"> Phase 3 — Prove it's trustworthy

**The uncomfortable question: how do you actually know it's any good?**

Industry surveys through 2026 put privacy, data handling, and pricing fairness at the top of traveller concerns about AI — and warn that brands treating governance as a compliance afterthought lose trust faster than personalisation earns it. Trust is a feature, and features get tested.

- A golden set of travel queries with expected tool-call sequences, so regressions surface immediately
- **Tool-call accuracy per model** — finally answering *does Nemotron pick better tools than Gemini?* with numbers instead of vibes
- LLM-as-judge scoring for itinerary quality: is it realistic, is it grounded, does it contradict itself
- A hallucination check that greps every claim in the output against the retrieved rows
- **OpenTelemetry** tracing across the loop, so a slow or wrong answer can be traced to the exact tool call
- Inline citations in the chat — every fact carries the dataset row it came from, visible on hover
- A written data-handling note: what's stored, what isn't, what leaves your machine

**Done when:** you can say "this model is 12% better at tool selection" and produce the evidence.

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f3a8/512.webp" alt="🎨" width="25" height="25" align="absmiddle"> Phase 4 — A real frontend, and an API under it

Streamlit got this built fast and earned every bit of its place. But it's a prototyping tool in a product costume, and the ceiling is real: no streaming, no routing, limited layout control, and a rerun model that fights anything stateful.

- **FastAPI** backend — the tools and the agent loop lift out almost unchanged, which was always the plan
- **Next.js + TypeScript + Tailwind** frontend
- **Server-sent events** for token-by-token streaming, because watching a spinner for eight seconds feels broken even when it isn't
- Interactive maps with the itinerary drawn as an actual route, not a list of names
- Drag-to-reorder days — everyone's first instinct on seeing a plan is to rearrange it
- Proper accessibility: keyboard navigation, screen-reader labels, WCAG-compliant contrast
- Mobile-first, because trips get planned on phones in bed

**Done when:** the API is the product and the UI is just one client of it.

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f916/512.webp" alt="🤖" width="25" height="25" align="absmiddle"> Phase 5 — Multi-agent orchestration

One agent doing everything is the simplest thing that works. It isn't the best thing.

- **Planner** decomposes the request into sub-goals
- **Researcher** agents run in parallel — weather, hotels, attractions, all at once instead of in sequence
- **Critic** reviews the draft and pushes back: *six hours of driving on day two is not a holiday*
- **Budget agent** holds the constraint and objects when the plan drifts over
- A supervisor with real state management, hand-rolled first — then compared against LangGraph to find out what the framework actually buys, which is a far more interesting answer than adopting it blindly
- Parallel tool execution, since three independent lookups shouldn't take three round-trips

**Done when:** a complex multi-city request produces a better plan than the single agent, and you can show why.

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f9e0/512.webp" alt="🧠" width="25" height="25" align="absmiddle"> Phase 6 — Actual machine learning

This is where it stops being an LLM wrapper and starts being a data science project. The industry framing here is *preference anticipation* — systems that know what you want before you finish describing it.

- **Price prediction** — gradient boosting on hotel features to estimate fair rates for unlisted properties, and flag overpriced ones
- **Recommender** — collaborative filtering first, then a two-tower retriever for personalised destination suggestions
- **Traveller segmentation** — clustering on behaviour to learn preference archetypes instead of asking three dropdown questions
- **Review sentiment** — a fine-tuned transformer over hotel reviews surfacing *"great location, paper-thin walls"* rather than a 4.2 that tells you nothing
- **Seasonality and crowd forecasting** — time series predicting price surges and busy weeks
- **Route optimisation** — a genuine TSP solver over attraction coordinates, so a day minimises travel instead of merely listing places in a plausible order
- **Hybrid retrieval** — embeddings *alongside* the lexical scorer, specifically for free-text reviews where semantic search finally earns its keep

**Done when:** the recommendations measurably beat "highest rated in this city."

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f4ca/512.webp" alt="📊" width="25" height="25" align="absmiddle"> Phase 7 — A data foundation worth the name

Five CSVs are training wheels. IDC's diagnosis is unambiguous: without a unified, real-time view, agentic AI can't deliver, and fragmented data produces generic offers.

- **Airflow** DAGs for scheduled ingestion and refresh
- **dbt** for transformations that are tested, documented, and reviewable
- **PostgreSQL + PostGIS** for geospatial queries — *"attractions within 5 km of my hotel"* becomes one query instead of a Python loop
- **DuckDB** for fast local analytics over dumps too big for pandas
- **Apache Iceberg** for versioned, time-travelled tables — so "what did this data look like in March?" is answerable
- **Great Expectations** quality gates that fail loudly at ingestion rather than quietly at inference
- Change-data-capture on live sources, so the data stops being a snapshot from a Kaggle upload

**Done when:** adding a new city or country is a config change, not a project.

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f30f/512.webp" alt="🌏" width="25" height="25" align="absmiddle"> Phase 8 — Global, spoken, and accessible to everyone

Travel is the most global thing there is, and this app currently speaks one language and covers one country. That's the biggest gap in the whole project.

- **Multilingual planning** — Hindi, Bengali, Tamil, Telugu, Marathi first, then Spanish, French, Arabic, Japanese, Mandarin. Not translated output bolted on afterwards: the retrieval and the prompts speak the language natively
- **Voice, both directions** — speak your request, hear the plan read back in your own language and accent. This matters far beyond convenience: it opens the app to travellers with low literacy, low vision, or simply a phone in one hand and a suitcase in the other
- **A live travel companion** — voice help *during* the trip, not just before it. *"My train is cancelled, what now?"* and the agent re-plans the day around the disruption
- **Culturally accurate localisation** — Deloitte's 2026 outlook notes travellers will pay more for culturally accurate interactions, and an agent that recommends a temple visit without mentioning the dress code isn't being helpful
- **Currency, units, and date formats** that follow the user, not the developer
- **Offline mode** via local models through Ollama, for aeroplanes, remote regions, and anyone who'd rather their itinerary didn't leave the device
- **Accessibility as a requirement, not a milestone** — screen readers, high contrast, reduced motion, large text, one-handed operation

**Done when:** someone plans a trip through this app, in their own language, by speaking to it, in a country you've never visited.

---

### <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f517/512.webp" alt="🔗" width="25" height="25" align="absmiddle"> Phase 9 — Join the agentic web

The most important structural shift of 2026 wasn't a new model. It was standardisation. MCP was donated to the Linux Foundation's Agentic AI Foundation in December 2025 with OpenAI, Google, Microsoft and AWS backing it — competing companies agreeing on one protocol, with SDK downloads well past a hundred million a month.

The eleven tools here are already the right shape for it. That's not a coincidence; it's what a clean tool registry gets you.

- **Expose the tools as an MCP server**, so any MCP-capable client can plan a trip using your data
- **Consume MCP servers** in turn — flight search, booking, calendar, maps — without writing another integration by hand
- **Agent-to-agent coordination** (A2A) so this planner can negotiate with a hotel's agent rather than scraping its website
- **Agentic commerce** — the direction the whole industry is pointing: agents that book, not just suggest. Which raises the real question, spend authority, and answering it properly means confirmation flows, budget ceilings, and an audit trail
- **Guardrails, deliberately.** The enterprise MCP research is blunt: the protocol gives you interoperability, *not* trustworthiness — that still has to be engineered in. Tool-poisoning benchmarks found capable models were often *more* susceptible, because the attack exploits good instruction-following. So: input validation, least privilege, honest tool descriptions, rate limits, and never passing user content anywhere near a shell

**Done when:** another agent can use your tools, and yours can use theirs, safely.

---

## <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f3af/512.webp" alt="🎯" width="30" height="30" align="absmiddle"> One last thought

The most valuable thing here isn't the itinerary generator.

It's that when the vendors fell over — an org policy locking the account, a model nobody was hosting, a retirement mid-build, an undocumented requirement in a brand-new API — **the project didn't stop.** Not because any of it was predicted. Because nothing was welded to a single API.

Everything on that roadmap, from voice in nine languages to agents negotiating with other agents, is downstream of getting that one boring architectural decision right.

That's the actual lesson. Not *how do I call an LLM*, but *how do I build something that outlives the LLM I called?*

<div align="center">

<br>

<img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f9f1/512.webp" alt="🧱" width="22" height="22" align="absmiddle"> **Built with stubbornness, five libraries, and an unreasonable number of 404s.**

*If it isn't in the data, it doesn't go in the plan.*

<br>

<img src="https://fonts.gstatic.com/s/e/notoemoji/latest/2b50/512.webp" alt="⭐" width="22" height="22" align="absmiddle"> *Star it if it's useful. Fork it if you can do better.*
*Open an issue if it lies to you — it really isn't supposed to.*

</div>

---

<div align="center">
<sub>

Attraction and hotel data from Kaggle · Weather by [Open-Meteo](https://open-meteo.com) · Places by [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org) · Rates by [Frankfurter](https://frankfurter.app)
<br>
Every live API here is free and needs no key. Please respect Nominatim's rate limits — volunteers run it.
<br>
Animated emoji from [Google Noto Animated Emoji](https://googlefonts.github.io/noto-emoji-animation/) · Brand marks from [Simple Icons](https://simpleicons.org)

</sub>
</div>
