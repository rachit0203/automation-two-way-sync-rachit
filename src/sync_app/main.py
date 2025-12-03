import argparse
import os
from .app import run_polling_loop
from .config import Config
from .logger import get_logger
from .sync_logic import SyncService


def main():
    parser = argparse.ArgumentParser(description="Two-way sync CLI")
    parser.add_argument("command", choices=["sync-once", "poll", "serve", "validate"], help="Run a single sync, start polling, run API server, or validate connectivity")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    cfg = Config()
    logger = get_logger("cli", cfg.log_level)
    # Validate configuration up-front to fail fast with clear error
    cfg.validate()

    if args.command == "sync-once":
        SyncService(cfg).run_full_sync_cycle()
        logger.info("Sync complete")
    elif args.command == "poll":
        run_polling_loop()
    elif args.command == "serve":
        import uvicorn
        uvicorn.run("sync_app.app:app", host=args.host, port=args.port, reload=False)
    elif args.command == "validate":
        from .lead_client import AirtableLeadClient
        from .task_client import TrelloTaskClient
        ok = True
        try:
            leads = AirtableLeadClient(cfg).list_leads()
            logger.info(f"Airtable OK: fetched {len(leads)} leads")
        except Exception as e:
            ok = False
            logger.error(f"Airtable connectivity failed: {e}. Check AIRTABLE_API_TOKEN scopes (data.records:read/write), AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME.")
        try:
            tasks = TrelloTaskClient(cfg).list_tasks()
            logger.info(f"Trello OK: fetched {len(tasks)} tasks across lists")
        except Exception as e:
            ok = False
            logger.error(f"Trello connectivity failed: {e}. Check TRELLO_API_KEY and TRELLO_API_TOKEN, and that list IDs belong to the board accessible by your token.")
        if ok:
            logger.info("Validation passed for both Airtable and Trello.")
        else:
            logger.error("Validation failed. Fix .env and retry.")


if __name__ == "__main__":
    main()
