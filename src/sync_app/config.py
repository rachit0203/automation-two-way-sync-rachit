from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    airtable_api_token: str = os.getenv("AIRTABLE_API_TOKEN", "")
    airtable_base_id: str = os.getenv("AIRTABLE_BASE_ID", "")
    airtable_table_name: str = os.getenv("AIRTABLE_TABLE_NAME", "Leads")

    trello_api_key: str = os.getenv("TRELLO_API_KEY", "")
    trello_api_token: str = os.getenv("TRELLO_API_TOKEN", "")
    trello_board_id: str = os.getenv("TRELLO_BOARD_ID", "")
    trello_list_todo_id: str = os.getenv("TRELLO_LIST_TODO_ID", "")
    trello_list_in_progress_id: str = os.getenv("TRELLO_LIST_IN_PROGRESS_ID", "")
    trello_list_done_id: str = os.getenv("TRELLO_LIST_DONE_ID", "")

    poll_interval_seconds: int = int(os.getenv("SYNC_POLL_INTERVAL_SECONDS", "30"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def validate(self) -> None:
        missing = []
        for key, value in self.__dict__.items():
            if key.endswith("_id") or key.endswith("_token") or key.endswith("_key"):
                if not value:
                    missing.append(key)
        if missing:
            raise ValueError(f"Missing required config values: {', '.join(missing)}")
