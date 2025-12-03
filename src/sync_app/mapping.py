from .models import LeadStatus, TaskStatus

STATUS_MAP_LEAD_TO_TASK = {
    LeadStatus.NEW: TaskStatus.TODO,
    LeadStatus.CONTACTED: TaskStatus.IN_PROGRESS,
    LeadStatus.QUALIFIED: TaskStatus.DONE,
    LeadStatus.LOST: TaskStatus.DONE,
}

STATUS_MAP_TASK_TO_LEAD = {
    TaskStatus.TODO: LeadStatus.NEW,
    TaskStatus.IN_PROGRESS: LeadStatus.CONTACTED,
    TaskStatus.DONE: LeadStatus.QUALIFIED,
}
