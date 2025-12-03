from src.sync_app.mapping import STATUS_MAP_LEAD_TO_TASK, STATUS_MAP_TASK_TO_LEAD
from src.sync_app.models import LeadStatus, TaskStatus


def test_lead_to_task_mapping():
    assert STATUS_MAP_LEAD_TO_TASK[LeadStatus.NEW] == TaskStatus.TODO
    assert STATUS_MAP_LEAD_TO_TASK[LeadStatus.CONTACTED] == TaskStatus.IN_PROGRESS
    assert STATUS_MAP_LEAD_TO_TASK[LeadStatus.QUALIFIED] == TaskStatus.DONE


def test_task_to_lead_mapping():
    assert STATUS_MAP_TASK_TO_LEAD[TaskStatus.TODO] == LeadStatus.NEW
    assert STATUS_MAP_TASK_TO_LEAD[TaskStatus.IN_PROGRESS] == LeadStatus.CONTACTED
    assert STATUS_MAP_TASK_TO_LEAD[TaskStatus.DONE] == LeadStatus.QUALIFIED
