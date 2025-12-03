# Two-way Sync: Airtable Leads ↔ Trello Tasks

Overview
- Python automation that keeps Airtable "Leads" in sync with Trello "Tasks".
- One lead maps to one Trello card via a stable "LeadID: <airtable_record_id>" marker.
- Uses REST APIs of Airtable and Trello (free tiers).

Architecture & Flow
- Lead Tracker: Airtable table with fields: name, email, status, source.
- Work Tracker: Trello board with three lists: TODO, IN_PROGRESS, DONE.
- Status mapping:
  - NEW → TODO
  - CONTACTED → IN_PROGRESS
  - QUALIFIED → DONE
  - LOST → DONE (card stays done; lead considered closed)
- Reverse mapping:
  - TODO → NEW
  - IN_PROGRESS → CONTACTED
  - DONE → QUALIFIED
- Idempotency: We search Trello for an existing card with `LeadID: <lead_record_id>` in description before creating.
- Sync loop: initial sync (create missing tasks), lead→task updates, task→lead updates.

Diagram (Mermaid)
```mermaid
flowchart LR
  A[Airtable Lead\n(name, email, status, source)] -- list/read --> S{Sync Service}
  S -- create/update --> T[Trello Card\n(title, list, desc LeadID)]
  T -- list/move --> S
  S -- update status --> A
```

Setup Instructions
1) Create/free accounts
- Airtable: create a base and a table named `Leads` with columns: name, email, status, source.
- Trello: create a board with lists for TODO, IN_PROGRESS, DONE.
2) API keys and IDs
- Copy `.env.sample` to `.env` and fill values:
  - `AIRTABLE_API_TOKEN`: go to Airtable account, create personal access token.
  - `AIRTABLE_BASE_ID`: from Airtable API docs for your base.
  - `AIRTABLE_TABLE_NAME`: default `Leads`.
  - `TRELLO_API_KEY`, `TRELLO_API_TOKEN`: from https://trello.com/app-key
  - `TRELLO_BOARD_ID`: board id (from Trello URL or API).
  - `TRELLO_LIST_TODO_ID`, `TRELLO_LIST_IN_PROGRESS_ID`, `TRELLO_LIST_DONE_ID`: list IDs.
   - Airtable token scopes: ensure `data.records:read` and `data.records:write` for the target base.
   - Tip: confirm base access by listing records via Airtable API docs (or `Invoke-RestMethod`).
3) Install dependencies
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Usage
- Run one sync:
```powershell
python -m src.sync_app.main sync-once
```
- Validate connectivity (Airtable + Trello):
```powershell
python -m src.sync_app.main validate
```
- Polling loop:
```powershell
python -m src.sync_app.main poll
```
- FastAPI server (health + manual sync):
```powershell
python -m src.sync_app.main serve --host 0.0.0.0 --port 8000
```
- Manual sync trigger:
```powershell
Invoke-RestMethod -Uri http://localhost:8000/sync -Method POST
```

Simulate changes
- Create/update a lead in Airtable and set `status`. The corresponding Trello card will be created/moved based on mapping.
- Move a Trello card between lists (or mark done). The corresponding Airtable lead `status` will be updated.

Assumptions & Limitations
- Uses description text to store `LeadID`. A Trello custom field could be used if available.
- Basic pagination for Airtable; Trello lists are iterated manually.
- Webhooks not configured due to simplicity; polling is provided. You can add webhooks later.

Error handling & Idempotency
- Retries (tenacity) for transient API errors.
- Per-record try/except: bad records logged and skipped; sync continues.
- Idempotent `ensure_task` prevents duplicates.

AI Usage Notes
- Tools: Copilot (this assistant) to scaffold modules, draft clients, and README.
- Used AI for status mapping suggestions and HTTP client patterns.
- Change/reject example: AI proposed using Trello custom fields; rejected to keep setup simpler with description marker.
- See `/ai-notes/` for exported prompts (optional).

Video
- Google Drive link: add your recorded demo here with "Anyone with Link" access.
