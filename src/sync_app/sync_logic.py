from typing import List
from tenacity import RetryError
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
                title = f"📋 Follow up: {lead.get('name')}"
                notes_parts = [
                    f"LeadID: {lead.get('id')}",
                    "",
                    "👤 Contact Information:",
                    f"Name: {lead.get('name')}",
                    f"Email: {lead.get('email')}",
                    "",
                    f"📊 Current Status: {lead_status.value if hasattr(lead_status, 'value') else lead_status}",
                ]
                if lead.get('source'):
                    notes_parts.extend(["", f"📍 Source: {lead.get('source')}"])
                notes_parts.extend(["", "---", "🔄 Synced from Airtable"])
                notes = "\n".join(notes_parts)
                self.tasks.ensure_task(title=title, lead_id=lead.get("id"), status=task_status, notes=notes)
            except RetryError as re:
                try:
                    last_exc = re.last_attempt.exception()
                except Exception:
                    last_exc = None
                self.logger.error(
                    f"initial_sync failed for lead {lead.get('id')}: RetryError: {re}; last_exception: {last_exc}"
                )
            except Exception as e:
                self.logger.error(f"initial_sync failed for lead {lead.get('id')}: {repr(e)}")

    def lead_to_task_updates(self) -> None:
        leads = self.leads.list_leads()
        for lead in leads:
            try:
                lead_status_raw = lead.get("status")
                lead_status = (
                    lead_status_raw
                    if isinstance(lead_status_raw, LeadStatus)
                    else LeadStatus(lead_status_raw)
                )
                desired_status = STATUS_MAP_LEAD_TO_TASK.get(lead_status)
                if not desired_status:
                    continue
                existing = self.tasks.find_task_by_lead_id(lead.get("id"))
                if existing and existing.get("status") != desired_status:
                    self.tasks.update_task_status(existing.get("id"), desired_status)
            except RetryError as re:
                try:
                    last_exc = re.last_attempt.exception()
                except Exception:
                    last_exc = None
                self.logger.error(
                    f"lead_to_task_updates failed for lead {lead.get('id')}: RetryError: {re}; last_exception: {last_exc}"
                )
            except Exception as e:
                self.logger.error(f"lead_to_task_updates failed for lead {lead.get('id')}: {repr(e)}")

    def task_to_lead_updates(self) -> None:
        tasks = self.tasks.list_tasks()
        for t in tasks:
            if not t.get("leadId"):
                continue
            try:
                task_status_raw = t.get("status")
                task_status = (
                    task_status_raw
                    if isinstance(task_status_raw, TaskStatus)
                    else TaskStatus(task_status_raw)
                )
                desired_lead_status = STATUS_MAP_TASK_TO_LEAD.get(task_status)
                if desired_lead_status:
                    self.leads.update_lead_status(t.get("leadId"), desired_lead_status)
                    sync_note = f"🔄 Status updated from Trello: {task_status.value} → {desired_lead_status.value}"
                    try:
                        self.leads.append_note(t.get("leadId"), sync_note)
                    except Exception as note_err:
                        self.logger.warning(f"Could not append note to lead {t.get('leadId')}: {note_err}")
            except RetryError as re:
                try:
                    last_exc = re.last_attempt.exception()
                except Exception:
                    last_exc = None
                self.logger.error(
                    f"task_to_lead_updates failed for lead {t.get('leadId')}: RetryError: {re}; last_exception: {last_exc}"
                )
            except Exception as e:
                self.logger.error(f"task_to_lead_updates failed for lead {t.get('leadId')}: {repr(e)}")

    def run_full_sync_cycle(self) -> None:
        self.initial_sync()
        self.lead_to_task_updates()
        self.task_to_lead_updates()
