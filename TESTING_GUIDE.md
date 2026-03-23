# Slack Bot Testing Guide

## Quick Start

The bot is now running with comprehensive debug logging. Follow these steps to test and debug the message flow.

---

## Step 1: Send a Test Message

### Option A: Send to a Channel (Easiest)
1. Go to any Slack channel where the bot is a member
2. Send a message: `hello bot` or `what can you do?`
3. The bot will now process it WITHOUT requiring @mention

### Option B: Send a Direct Message
1. Open Direct Messages and find the bot
2. Send any message
3. Watch the bot respond

---

## Step 2: Watch the Debug Logs

Look for logs that follow this pattern:

```
STEP 0: Message event received ===
STEP 1: Raw event extracted | user=U..., channel=C..., text=...
STEP 1: Valid message from U... in C...
STEP 2: Processing channel message without explicit mention
STEP 2: Cleaned text = '...'
STEP 3: Beginning agent processing
```

---

## Step 3: Identify Where It Stops

### ✅ SUCCESS (Full Flow)
If you see all steps including:
```
STEP 6: SUCCESSFULLY SENT TO SLACK ✅
```
**Congratulations!** The bot is working end-to-end.

---

### ❌ STOPS at STEP 2

**Problem**: Bot still not processing channel messages

**Solution**: Check if the message looks like a command (help, summarize, remind, etc.) - those are special cases.

Try a plain message: `tell me about the project`

---

### ❌ STOPS at STEP 3 or 3x

**Problem**: Session/context creation failing

**Logs will show**:
```
[ERROR] ❌ AGENT PROCESSING FAILED: ... (error message)
```

**Common fixes**:
- Check the database is initialized: `sqlite3 data/maantra.db ".tables"` should show tables
- Verify user exists in Slack
- Check channel exists

**Action**: Share the full error message from logs

---

### ❌ STOPS at STEP 4

**Problem**: Agent is crashing or hanging

**Logs will show**:
```
STEP 4: CALLING AGENT with message: '...'
(then nothing, or error)
```

**Common fixes**:
- Agent config missing
- Agent dependencies not installed
- Invalid LLM API key

**Check agent code**: `src/agents/agent.py`

**Action**: Share the error or timeout message

---

### ❌ STOPS at STEP 5

**Problem**: Response generated but Slack send failed

**Logs will show**:
```
STEP 4: AGENT RETURNED | response.content=...
STEP 5: SENDING RESPONSE TO SLACK
(then error)
```

**Common fixes**:
- Slack token issues
- Channel permission denied
- Message too long

**Action**: Share the Slack API error

---

## Step 4: Share Complete Logs

When reporting an issue, provide:

1. **Full log output** from STEP 0 to where it fails
2. **Any error messages** (they start with `[ERROR]`)
3. **What message you sent** to the bot
4. **Which channel/DM** you sent it to

---

## Manual Testing Commands

Once the bot responds to regular messages, try these:

| Command | Expected Behavior |
|---------|-------------------|
| `help` | Shows help menu |
| `summarize` | (in a thread) Summarizes thread |
| `I have a question` | Agent responds with answer |
| `/approve [code]` | Slash command handler |

---

## Debug Logs Location

**Live logs**: Terminal where you ran `uv run python -m src.main`

**Log file**: `logs/` directory (if configured)

To see only bot logs:
```bash
grep "maantra.slack" logs/* 2>/dev/null | tail -50
```

---

## Restart Bot with Fresh Start

```bash
# Kill current bot (Ctrl+C in terminal)

# Clear any cached state (optional)
rm -f data/maantra.db  # WARNING: deletes session data

# Restart
uv run python -m src.main
```

---

## Next Steps Based on Results

**If bot works end-to-end**:
- ✅ Core setup is correct
- Next: Test agent responses for quality
- Check: Agent memory, RAG context, MCP tools

**If bot fails somewhere**:
1. Share logs showing exact failure point
2. We'll fix that specific component
3. Re-test the flow
4. Move to next component

---

## Questions?

When asking for help, include:
- Console output from STEP 0 to failure
- The exact message you sent
- Any error text from logs

**Let's go! Send a test message and share the logs.**
