# Getting Started: running the project in Claude Code (beginner walkthrough)

You're on a Mac, working solo, with 7 days left (today is Oct 9, due Oct 16). This guide takes you from an empty folder to a running pipeline. Claude Code writes and runs the code; your job is to **review, approve, and make the judgment calls**.

---

## Part 1: What Claude Code is (2-minute mental model)

- It's a chat that lives in your **terminal** and can read your project's files, write code, and run commands.
- You start it by typing `claude` **inside your project folder**. That folder is its whole world.
- Before it edits a file or runs a command, it **asks permission**. You'll see a prompt with options such as Yes, Yes and don't ask again, and No. For this project: read what it wants to do, approve normal file edits and `pytest`, `pip` and `python` commands, and say No (and ask why) if it wants to delete things or touch files outside this folder.
- It reads `CLAUDE.md` automatically at the start of each session. That file is the project's memory. Chat history is **not** remembered between sessions, but `CLAUDE.md` and your files are.
- Press **Esc** to interrupt it if it goes off track. Type `/help` inside a session to see the current commands, since they change over time.

Useful commands (type them inside a Claude Code session):

| Command | What it does |
|---|---|
| `/clear` | Wipe the conversation and start fresh (files and `CLAUDE.md` stay) |
| `/help` | Show available commands |
| `/exit` (or Ctrl+C twice) | Leave Claude Code |

To leave and later pick up a previous conversation, run `claude --continue` (or `claude --resume` to choose one) instead of plain `claude`.

---

## Part 2: One-time setup (about 20 minutes)

### 2.1 Open Terminal
Press Cmd+Space, type "Terminal", press Enter. Everything below is typed there, **not** inside Claude Code, unless it says so.

### 2.2 Check what's installed
```bash
claude --version     # Claude Code (you already ran it, so this should work)
git --version        # if a pop-up offers to install developer tools, click Install
python3 --version    # you want 3.11 or newer
```
If `python3` is older than 3.11 or missing, tell me, or install a current version from python.org or with `brew install python`.

### 2.3 Get your keys and email ready (you'll paste these into a file later)
- **Your email address.** Crossref, Europe PMC and Unpaywall are polite-use APIs and ask for contact info.
- **CORE API key (free).** Search "CORE API key" on core.ac.uk and register. You only need it at prompt 03, but registering now saves time.
- **Anthropic API key for the LLM judge step.** That step runs from your code and uses API credits separately from Claude Code. Needed around Oct 13, not before. Check whether your ASU account provides one.

### 2.4 Set up the project folder
```bash
cd ~/consciousness-excavator
git init
mkdir prompts reports
```
Download the files from this kit, then copy them in. Adjust paths if your browser saved them elsewhere:
```bash
cp ~/Downloads/CLAUDE.md .
cp ~/Downloads/01_level1_scraper.md prompts/
cp ~/Downloads/02_corpus_and_level2.md prompts/
cp ~/Downloads/03_add_core_source.md prompts/
cp ~/Downloads/GETTING_STARTED.md .
ls -R
```
If a file downloaded as `CLAUDE (1).md`, rename it so it is exactly `CLAUDE.md` (the name is case-sensitive).

Make a first save point:
```bash
git add -A
git commit -m "Project setup: CLAUDE.md and stage prompts"
```

### 2.5 Public data only
Your university has AI governance rules. This project uses only public sources (LoC, Europe PMC, Crossref, Unpaywall, CORE). Don't put anything sensitive or student-related in this repo or any prompt.

---

## Part 3: Run Prompt 01 (Level 1), today

**Start the session:**
```bash
cd ~/consciousness-excavator
claude
```

**Message 1 (checks that CLAUDE.md loaded):**
> Read CLAUDE.md and summarize the project back to me: the three levels, the five theories, the sources, and the working rules.

If the summary is right, continue. If not, tell it what's wrong and ask it to re-read.

**Message 2:**
> Read prompts/01_level1_scraper.md and follow it step by step. Stop at every checkpoint and wait for me.

(Telling it to read the file is more reliable than pasting a long prompt into the terminal.)

**What happens and what you do at each checkpoint:**

| Checkpoint | What you check | If it's wrong |
|---|---|---|
| **Step 0 scaffold** | Folder structure exists, `.env.example` and `.gitignore` created | Ask it to fix it |
| **Step 1 site inspection** | It found all 5 theory pages with the right titles; raw reference examples look like real citations; robots.txt allows it | If a theory is missing or the page needs JavaScript rendering, answer its question or ask it to propose options |
| **Step 2 parsing** | Read the 10 random parsed references per theory next to the raw text. Do titles, authors and years match? | Tell it exactly which kind of reference is broken, and ask for a fix plus a test |
| **Step 3 resolution** | Spot-check a few matches in the output: does the DOI's paper really match the reference? | Ask it to raise the match threshold |
| **Step 4 report** | Read `reports/level1_resolution.md` | Send it to me |

**Before it needs your email:** copy `.env.example` to `.env` and fill it in:
```bash
cp .env.example .env
open -e .env
```
Type your email and save. `.env` is gitignored, so it won't be committed.

When Step 4 is done:
```bash
git status
git log --oneline
```
You should see commits from each step. Then type `/exit`.

**Send me** the per-theory table from `reports/level1_resolution.md`. It tells us whether any theory has too few full-text seeds.

---

## Part 4: Run Prompt 02 (corpus + Level 2), Oct 10

**First, do your homework (30-45 min):** write your own notes for each theory: the names and synonyms, key authors, and 3-5 sentences on its core claims in your own words. Claude Code will propose a `terms.yaml`, and you'll edit it using these notes. The semiotic account needs the most care.

**Start a fresh session** (`claude` in the project folder), then:
> Read CLAUDE.md, then read prompts/02_corpus_and_level2.md and follow it step by step. Stop at every checkpoint and wait for me.

**Checkpoints to watch:**
1. **Step 0 (API test queries):** it will propose per-article downloads or bulk downloads. Pick the one with the shorter estimated time. If the estimate is over a few hours, ask it to lower the caps.
2. **Step 1 (corpus built):** check corpus size per part, year range (should be 1995-2015 only), and the 5 random sample papers.
3. **Step 2 (`terms.yaml`):** open it with `open -e src/terms.yaml`. Edit by hand: remove terms that are too generic, add synonyms you know, check the abbreviations. Then tell Claude Code to continue.
4. **Step 6 (precision audit):** for 20 hits per theory, mark each snippet as a true or false positive. If a term has poor precision, tell it which to demote.

Long downloads can take a while. You can leave it running and work on your notes, but come back to approve permission prompts, since it will pause waiting for you.

**Send me** the seed recall numbers and the theory overlap table from `reports/level2_terms.md`.

---

## Part 5: Run Prompt 03 (CORE), Oct 11, only if the go/no-go says so

> Read CLAUDE.md, then read prompts/03_add_core_source.md and follow it step by step. Stop at every checkpoint and wait for me.

Step 0 recommends go or no-go from your Level 1 and Level 2 numbers. **If it says no-go, or if you're behind schedule, skip CORE entirely.** It's the first thing to cut, and mentioning it as future work is fine.

---

## Part 6: What comes next (I'll write these when you're ready)

- **Prompt 04:** chunking, embeddings, concept profiles, Level 3 retrieval with direct-term exclusion and contrastive scoring (Oct 11-12)
- **Prompt 05:** evaluation, with hold-out recall and the discriminability matrix (Oct 12)
- **Prompt 06:** LLM judge on the top ~30 per theory (Oct 13)
- **Prompt 07:** window and prediction experiment (Oct 14)
- **Prompt 08:** Streamlit UI and demo script (Oct 15)

For prompt 04 I'll need to know your Mac's chip (Apple Silicon or Intel) and RAM. Run `system_profiler SPHardwareDataType | grep -E "Chip|Memory"` and send me the output. That decides which embedding model is practical.

---

## Part 7: Good habits and troubleshooting

**Habits**
- **One stage per session.** Start with `claude`, finish the stage, `/exit`. A fresh session reloads `CLAUDE.md` and stays focused.
- **Commit after every step** (Claude Code is told to, but check with `git log --oneline`). Commits are your undo history.
- **Read the printed sanity checks.** If counts look strange (zero results, 100% resolution), question it before moving on.
- **Check samples yourself.** The parsing review and precision audit are the two places only you can catch errors.

**If something goes wrong**
| Problem | Fix |
|---|---|
| "Error reading file" or it can't find CLAUDE.md | You're in the wrong folder. Check with `pwd` and `ls`. Exit, `cd ~/consciousness-excavator`, run `claude` again |
| It forgot the project context | `/clear`, then: "Read CLAUDE.md and prompts/0X... and continue from Step N" |
| It's looping or going off track | Press Esc, say what's wrong, and ask it to propose a plan before acting |
| A command fails with a network error | Tell it the exact error message. Your organization may restrict network access, so you may need to contact your IT admin |
| A download is very slow | Ask it to lower the caps in config, or to switch to the bulk method |
| It wants to install a lot of packages | Fine inside `.venv`. Say no if it tries to install system-wide |
| A step breaks something that worked | `git log --oneline`, then ask Claude Code to revert that commit, or send me the error |
| You're short on time | Follow the cut order in CLAUDE.md: CORE, then hand-labeling, then the 1995-2025 window |

**What to bring back to me after each stage**
1. The report file's key tables (Level 1 resolution, Level 2 seed recall and overlap).
2. Any error you can't resolve in a couple of tries.
3. Your edited `terms.yaml` or concept notes, if you want critique.
