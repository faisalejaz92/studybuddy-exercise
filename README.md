# StudyBuddy - Senior AI Engineer Code Exercise

## What This Is

This is a take-home coding exercise for the **Senior AI Engineer** position. You'll
work on a realistic AI agent codebase, choosing which problems to solve and how
to solve them.

**We expect you to use AI tools** (Claude, Cursor, Copilot, etc.) - this reflects
how we actually work. Part of what we're evaluating is how effectively you
collaborate with AI to ship quality code.

**Time:** ~3 hours total. If you go significantly over, stop and submit what you
have. We'd rather see incomplete but thoughtful work than a rushed attempt to
finish everything.

## Before You Start

**Privacy:** Prefer not to fork publicly? Clone to a private repo and share
access.

**New to LangGraph?** Don't worry - see the [Quick Reference](#langgraph-quick-reference)
section. The codebase is straightforward and well-structured.

## The Scenario

StudyBuddy is an early-stage edtech startup building an AI study assistant.
You're joining the team 2 weeks before beta launch with 100 users.

The agent works - users can chat and search their notes. But the team has
identified gaps that need addressing before launch.

## Quick Start

1. Clone and setup:
   ```bash
   git clone <repo>
   cd studybuddy
   cp .env.example .env
   # Add your OPENAI_API_KEY to .env
   ```

2. Install and run backend:
   ```bash
   uv sync
   make dev  # LangGraph server on :2024
   ```

3. Install and run frontend:
   ```bash
   cd web && npm install && npm run dev  # Next.js on :3000
   ```

4. Open http://localhost:3000 and chat with StudyBuddy

---

## The Exercise

Choose 1-2 issues to work on. **Quality over quantity.**

These are real product problems, not specification documents. Part of the
exercise is figuring out what to build.

---

### Issue 1: "Users forget what they studied" (~1.5 hrs)

**From the PM:**

> "Users are telling us they forget what they learned after a session ends.
> We need something that helps them retain knowledge. Sarah from Support
> suggested flashcards, but I'm open to other ideas. What can we ship
> before beta?"

**What exists:**
- `graph/tools/notes.py` - search_notes tool that works
- No learning reinforcement features yet

**Considerations:**
- Flashcards are one option, but many other things could also work (e.g. quizzes,
  summaries, spaced repetition prompts, etc.)
- How should the agent know when to use this capability?
- What's a reasonable MVP scope for 1.5 hours?
- What tradeoffs are you making? (complexity, persistence, polish)

---

### Issue 2: "Support can't help users" (~1 hr)

**From the PM:**

> "Support is complaining they can't help users who report issues. When
> someone says 'the agent gave me a weird answer,' we have no way to see
> what happened. We need visibility before beta launch."

**What exists:**
- LangGraph stores conversation threads (checkpoints)
- `GET /threads` API returns thread list
- `GET /threads/{id}/state` returns conversation messages
- Chat UI works at `/`, no admin UI exists

**Considerations:**
- What data is useful to surface? Messages only? Tool calls? Errors?
- Who is the primary user - Support? Engineers? Both?
- What's the right UX tradeoff for a 1-hour implementation?
- How do you handle loading and error states?

---

### Issue 3: "We can't debug production issues" (~1 hr)

**From the Engineering Lead:**

> "Production debugging is painful right now - just print statements
> everywhere. Before we launch to 100 users, we need to be able to
> actually diagnose issues. We're not ready for full observability
> infrastructure, but we need something."

**What exists:**
- `print()` statements scattered in `graph/tools/notes.py` and `graph/main.py`
- No structured logging
- No request correlation across tool calls
- Logs go to stdout

**Considerations:**
- What's "enough" observability for 100 beta users?
- Structured JSON logging? Request tracing? Both?
- Which code paths are critical to instrument?
- How do you correlate logs across a single conversation turn?

---

## How You'll Be Evaluated

| Dimension | What We're Looking For |
|-----------|------------------------|
| **Problem Understanding** | Did you ask good questions (even to yourself)? Did you scope appropriately for the time? |
| **AI Collaboration** | Did you use AI tools strategically? Did you evaluate and refine AI suggestions? |
| **Code Quality** | Is the code production-ready? Does it handle errors? Did you add tests where appropriate? |
| **Communication** | Can you clearly explain your tradeoffs and decisions in the recording? |

We're not counting features or lines of code. A thoughtful, working
implementation of one issue beats incomplete attempts at all three.

## How to Submit

### Step 1: Fork and Code

1. **Fork** this repository (or clone to a private repo)
2. Create a branch for your work (e.g., `my-submission`)
3. Work the issues using your preferred AI tools
4. Commit and push your changes
   - Your commit history is visible and part of the evaluation
   - Incremental commits are better than one big commit

### Step 2: Record Your Work

**AI Workflow Recording (~5 min)**
- Screen capture showing your AI-assisted development on at least one issue
- We want to see: how you prompt, how you iterate, how you evaluate AI output
- Tools like Loom, QuickTime, or OBS work well

**Demo + Code Walkthrough (~5-10 min)**
- Demo what you built (show it working)
- Walk through your code and explain key decisions
- Note what you'd improve given more time

### Step 3: Submit

Email the following to your recruiter contact:
1. Link to your GitHub fork/branch
2. Link to AI workflow recording
3. Link to demo recording

**Deadline:** Complete within one week of receiving these instructions, or
contact your recruiter if you need more time.

---

## Reference

### Architecture

```
┌─────────────┐     ┌─────────────────┐
│   Next.js   │────▶│  LangGraph API  │
│   (Chat)    │     │  (Agent + Tools)│
└─────────────┘     └─────────────────┘
     :3000               :2024
```

- **LangGraph**: Agent orchestration with tool calling and thread persistence
- **Next.js**: Streaming chat UI using @langchain/langgraph-sdk

The dev server uses in-memory persistence for conversation threads.

### Project Structure

```
studybuddy/
├── graph/
│   ├── main.py                  # build_graph() - agent definition
│   ├── state.py                 # State schema
│   ├── config.py                # Runtime configuration
│   ├── tools/
│   │   └── notes.py             # search_notes tool
│   └── prompts/
│       └── system.py            # System prompt
│
├── web/
│   ├── app/
│   │   ├── page.tsx             # Chat interface
│   │   └── admin/               # Admin placeholder
│   └── components/
│       └── chat/                # Chat components
│
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
│
├── Makefile                     # dev, test commands
├── pyproject.toml               # Python dependencies
├── langgraph.json               # LangGraph configuration
└── .env.example                 # Environment template
```

### Development Commands

```bash
# From repository root
make dev          # Start LangGraph server (Studio at http://localhost:2024)
make sync         # Install Python dependencies
make test         # Run tests

# Frontend (from web/ directory)
npm run dev       # Start Next.js dev server (http://localhost:3000)
npm run build     # Build for production
```

### LangGraph Quick Reference

New to LangGraph? Here's what you need to know:

**Adding a tool:**
```python
# graph/tools/my_tool.py
from langchain_core.tools import tool

@tool
def my_tool(query: str) -> str:
    """Description of what this tool does."""
    return "result"
```

Then add it to the tools list in `graph/main.py`.

**Modifying the system prompt:**
Edit `graph/prompts/system.py` - the `SYSTEM_PROMPT` string is injected
into every conversation.

**How state flows:**
1. User message arrives
2. Agent node runs (LLM decides what to do)
3. If LLM calls a tool → tool executes → back to agent
4. If LLM responds → response returned to user

**Key files:**
- `graph/main.py` - Where the agent is built
- `graph/tools/notes.py` - Example tool implementation
- `graph/prompts/system.py` - System prompt

**Docs:** https://langchain-ai.github.io/langgraph/

### Troubleshooting

**Missing API key:**
Ensure `OPENAI_API_KEY` is set in your `.env` file.
