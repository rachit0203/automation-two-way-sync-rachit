import httpx
from typing import Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import Config
from .logger import get_logger
from .models import TaskStatus


class TrelloTaskClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.logger = get_logger(self.__class__.__name__, cfg.log_level)
        self.base_params = {"key": cfg.trello_api_key, "token": cfg.trello_api_token}
        self.api = "https://api.trello.com/1"

    def _list_cards_in_list(self, list_id: str) -> List[Dict]:
        r = httpx.get(f"{self.api}/lists/{list_id}/cards", params=self.base_params, timeout=20)
        if r.status_code != 200:
            body = r.text
            if r.status_code == 401:
                self.logger.error("Trello 401: invalid key/token or token lacks access to board/lists.")
            elif r.status_code == 403:
                self.logger.error("Trello 403: forbidden. Ensure token has board access and lists belong to specified board.")
            else:
                self.logger.error(f"Trello list cards error {r.status_code}: {body}")
            raise httpx.HTTPStatusError("Trello list cards failed", request=r.request, response=r)
        return r.json()

    def list_tasks(self) -> List[Dict]:
        tasks: List[Dict] = []
        for list_id, status in [
            (self.cfg.trello_list_todo_id, TaskStatus.TODO),
            (self.cfg.trello_list_in_progress_id, TaskStatus.IN_PROGRESS),
            (self.cfg.trello_list_done_id, TaskStatus.DONE),
        ]:
            if not list_id:
                continue
            for card in self._list_cards_in_list(list_id):
                raw_desc = card.get("desc")
                desc: str = str(raw_desc) if raw_desc is not None else ""
                lead_id = None
                if isinstance(desc, str) and "LeadID:" in desc:
                    try:
                        lead_id = desc.split("LeadID:")[-1].strip().splitlines()[0].strip()
                    except Exception:
                        lead_id = None
                tasks.append({
                    "id": card["id"],
                    "title": card["name"],
                    "status": status,
                    "leadId": lead_id or "",
                    "notes": desc,
                })
        return tasks

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def ensure_task(self, title: str, lead_id: str, status: TaskStatus, notes: Optional[str] = None) -> Dict:
        existing = self.find_task_by_lead_id(lead_id)
        if existing:
            self.update_task_status(existing["id"], status)
            return existing
        list_id = self._status_to_list_id(status)
        payload = {
            "name": title,
            "idList": list_id,
            "desc": f"LeadID: {lead_id}\n" + (notes or ""),
        }
        r = httpx.post(
            f"{self.api}/cards",
            params=self.base_params,
            data=payload,
            timeout=20,
        )
        if r.status_code != 200:
            body = r.text
            self.logger.error(f"Trello create card error {r.status_code}: {body}")
            raise httpx.HTTPStatusError("Trello create card failed", request=r.request, response=r)
        card = r.json()
        return {
            "id": card["id"],
            "title": card["name"],
            "status": status,
            "leadId": lead_id,
            "notes": card.get("desc") or "",
        }

    def _status_to_list_id(self, status: TaskStatus) -> str:
        if status == TaskStatus.TODO:
            return self.cfg.trello_list_todo_id
        if status == TaskStatus.IN_PROGRESS:
            return self.cfg.trello_list_in_progress_id
        if status == TaskStatus.DONE:
            return self.cfg.trello_list_done_id
        raise ValueError(f"Unknown TaskStatus: {status!r}")

    def find_task_by_lead_id(self, lead_id: str) -> Optional[Dict]:
        for t in self.list_tasks():
            if t.get("leadId") == lead_id:
                return t
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        list_id = self._status_to_list_id(status)
        r = httpx.put(f"{self.api}/cards/{task_id}", params={**self.base_params, "idList": list_id}, timeout=20)
        if r.status_code != 200:
            body = r.text
            self.logger.error(f"Trello move card error {r.status_code}: {body}")
            raise httpx.HTTPStatusError("Trello move card failed", request=r.request, response=r)

