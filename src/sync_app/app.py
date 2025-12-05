import time
from fastapi import FastAPI
from .config import Config
from .sync_logic import SyncService
from .logger import get_logger

app = FastAPI()
cfg = Config()
try:
    cfg.validate()
except Exception:
    pass
logger = get_logger("app", cfg.log_level)

sync_service = SyncService(cfg)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/sync")
async def trigger_sync():
    try:
        sync_service.run_full_sync_cycle()
        return {"status": "synced"}
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {"status": "error", "message": str(e)}


def run_polling_loop():
    logger.info("Starting polling loop")
    while True:
        try:
            sync_service.run_full_sync_cycle()
        except Exception as e:
            logger.error(f"Polling sync failed: {e}")
        time.sleep(cfg.poll_interval_seconds)
