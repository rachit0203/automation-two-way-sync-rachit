from typing import List
from .lead_client import AirtableLeadClient
from .task_client import TrelloTaskClient
from .mapping import STATUS_MAP_LEAD_TO_TASK, STATUS_MAP_TASK_TO_LEAD
from .logger import get_logger
from .config import Config
from .models import LeadStatus, TaskStatus


class SyncService:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.logger = get_logger(self.__class__.__name__, cfg.log_level)
        self.leads = AirtableLeadClient(cfg)
        self.tasks = TrelloTaskClient(cfg)

    def initial_sync(self) -> None:
        leads = self.leads.list_leads()
        relevant = [l for l in leads if (l.get("status") != LeadStatus.LOST)]
        for lead in relevant:
            try:
                lead_status = lead.get("status")
                task_status = STATUS_MAP_LEAD_TO_TASK.get(lead_status, TaskStatus.TODO)
                title = f"Follow up: {lead.get('name')}"
                notes = f"Email: {lead.get('email')}\nSource: {lead.get('source') or ''}"
                self.tasks.ensure_task(title=title, lead_id=lead.get("id"), status=task_status, notes=notes)
            except Exception as e:
                self.logger.error(f"initial_sync failed for lead {lead.get('id')}: {e}")

    def lead_to_task_updates(self) -> None:
        leads = self.leads.list_leads()
        for lead in leads:
            try:
                lead_status = lead.get("status")
                desired_status = STATUS_MAP_LEAD_TO_TASK.get(lead_status)
                if not desired_status:
                    continue
                existing = self.tasks.find_task_by_lead_id(lead.get("id"))
                if existing and existing.get("status") != desired_status:
                    self.tasks.update_task_status(existing.get("id"), desired_status)
            except Exception as e:
                self.logger.error(f"lead_to_task_updates failed for lead {lead.get('id')}: {e}")

    def task_to_lead_updates(self) -> None:
        tasks = self.tasks.list_tasks()
        for t in tasks:
            if not t.get("leadId"):
                continue
            try:
                task_status = t.get("status")
                desired_lead_status = STATUS_MAP_TASK_TO_LEAD.get(task_status)
                if desired_lead_status:
                    self.leads.update_lead_status(t.get("leadId"), desired_lead_status)
            except Exception as e:
                self.logger.error(f"task_to_lead_updates failed for lead {t.get('leadId')}: {e}")

    def run_full_sync_cycle(self) -> None:
        self.initial_sync()
        self.lead_to_task_updates()
        self.task_to_lead_updates()
