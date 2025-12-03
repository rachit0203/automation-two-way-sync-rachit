import httpx
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import Config
from .logger import get_logger
from .models import LeadStatus
from urllib.parse import quote


class AirtableLeadClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.logger = get_logger(self.__class__.__name__, cfg.log_level)
        table_path = quote(cfg.airtable_table_name, safe="")
        self.base_url = f"https://api.airtable.com/v0/{cfg.airtable_base_id}/{table_path}"
        self.headers = {
            "Authorization": f"Bearer {cfg.airtable_api_token}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def list_leads(self) -> List[Dict]:
        leads: List[Dict] = []
        offset: Optional[str] = None
        while True:
            params = {}
            if offset:
                params["offset"] = offset
            r = httpx.get(self.base_url, headers=self.headers, params=params, timeout=20)
            if r.status_code != 200:
                self.logger.error(f"Airtable list_leads error {r.status_code}: {r.text}")
                raise httpx.HTTPStatusError("Airtable list_leads failed", request=r.request, response=r)
            data = r.json()
            for rec in data.get("records", []):
                fields = rec.get("fields", {})
                # Normalize status to LeadStatus enum (default NEW)
                raw_status = (fields.get("status") or fields.get("Status") or "NEW").upper()
                try:
                    status = LeadStatus(raw_status)
                except Exception:
                    status = LeadStatus.NEW
                lead = {
                    "id": rec.get("id"),
                    "name": fields.get("name") or fields.get("Name") or "",
                    "email": fields.get("email") or fields.get("Email") or "",
                    "status": status,
                    "source": fields.get("source") or fields.get("Source") or None,
                }
                leads.append(lead)
            offset = data.get("offset")
            if not offset:
                break
        return leads

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def update_lead_status(self, lead_id: str, status) -> None:
        url = f"{self.base_url}/{lead_id}"
        # Accept enum or string
        status_value = status.value if hasattr(status, "value") else str(status)
        payload = {"fields": {"status": status_value}}
        r = httpx.patch(url, headers=self.headers, json=payload, timeout=20)
        if r.status_code not in (200):
            body = r.text
            self.logger.error(f"Airtable update_lead_status error {r.status_code}: {body}")
            raise httpx.HTTPStatusError("Airtable update_lead_status failed", request=r.request, response=r)

