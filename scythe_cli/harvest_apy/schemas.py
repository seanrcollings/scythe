import typing as t
import math
from datetime import date, datetime, time

import pydantic


class User(pydantic.BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    telephone: str
    timezone: str
    has_access_to_all_future_projects: bool
    is_contractor: bool
    is_admin: bool
    is_project_manager: bool
    can_see_rates: bool
    can_create_projects: bool
    can_create_invoices: bool
    is_active: bool
    weekly_capacity: int
    default_hourly_rate: t.Optional[float] = None
    cost_rate: t.Optional[float] = None
    roles: list[str]
    avatar_url: str
    created_at: datetime
    updated_at: datetime


class Project(pydantic.BaseModel):
    id: int
    client: t.Optional[dict] = None
    name: str
    code: str
    is_active: bool = True
    is_billable: bool
    is_fixed_fee: bool = False
    bill_by: t.Optional[str] = None
    hourly_rate: t.Optional[float] = None
    budget: t.Optional[float] = None
    budget_by: t.Optional[str] = None
    budget_is_monthly: bool = False
    notify_when_over_budget: bool = False
    over_budget_notification_percentage: t.Optional[float] = None
    over_budget_notification_date: t.Optional[date] = None
    show_budget_to_all: bool = False
    cost_budget: t.Optional[float] = None
    cost_budget_include_expenses: bool = False
    fee: t.Optional[float] = None
    notes: t.Optional[str]
    starts_on: t.Optional[date] = None
    ends_on: t.Optional[date] = None
    created_at: t.Optional[datetime] = None
    updated_at: t.Optional[datetime] = None


class Task(pydantic.BaseModel):
    id: int
    name: str
    is_active: bool
    billable_by_default: bool
    default_hourly_rate: float
    is_default: bool
    created_at: datetime
    updated_at: datetime


class TimeEntry(pydantic.BaseModel):
    id: int
    spent_date: date
    user: dict
    user_assignment: dict
    client: dict
    project: dict
    task: dict
    task_assignment: dict
    external_reference: t.Optional[dict]
    invoice: t.Optional[dict]
    hours: float
    hours_without_timer: float
    rounded_hours: float
    notes: t.Optional[str]
    is_locked: float
    locked_reason: t.Optional[str]
    is_closed: float
    is_billed: float
    timer_started_at: t.Optional[datetime]
    started_time: t.Optional[time]
    ended_time: t.Optional[time]
    is_running: float
    billable: float
    budgeted: float
    billable_rate: t.Optional[float]
    cost_rate: t.Optional[float]
    created_at: datetime
    updated_at: datetime

    def time(self) -> tuple[int, int]:
        minutes, hours = math.modf(self.hours)
        minutes = math.floor(round(minutes, 2) * 60)
        hours = int(hours)
        return hours, minutes

    def fmt_time(self) -> str:
        hours, minutes = self.time()
        minutes_str = str(minutes) if minutes >= 10 else f"0{minutes}"
        return f"{hours}:{minutes_str}"

    @pydantic.validator("started_time", pre=True)
    def parse_started_time(cls, v):
        if v is None:
            return v

        hour, minutes = (int(x) for x in v[0:-2].split(":"))
        day_period = v[-2:]
        if day_period == "pm":
            hour += 12

        return f"{hour}:{minutes}"


class TimeEntryParams(t.TypedDict):
    user_id: int
    client_id: int
    project_id: int
    task_id: int
    external_reference_id: str
    is_billed: bool
    is_running: bool
    updated_since: datetime
    # from:	date
    to: date
    page: int
    per_page: int


class TaskAssignment(pydantic.BaseModel):
    class TaskAssignmentTask(pydantic.BaseModel):
        id: int
        name: str

    id: int
    task: TaskAssignmentTask
    is_active: bool
    billable: t.Optional[bool] = None
    hourly_rate: t.Optional[float] = None
    budget: t.Optional[float] = None
    created_at: datetime
    updated_at: datetime


class ProjectAssignment(pydantic.BaseModel):
    id: int
    is_active: bool
    is_project_manager: bool
    use_default_rates: bool
    hourly_rate: t.Optional[float]
    budget: t.Optional[float]
    created_at: datetime
    updated_at: datetime
    project: Project
    task_assignments: list[TaskAssignment]
    client: dict
