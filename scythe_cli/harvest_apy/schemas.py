import typing as t
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
    client: dict
    name: str
    code: str
    is_active: bool
    is_billable: bool
    is_fixed_fee: bool
    bill_by: str
    hourly_rate: float
    budget: float
    budget_by: str
    budget_is_monthly: bool
    notify_when_over_budget: bool
    over_budget_notification_percentage: float
    over_budget_notification_date: date
    show_budget_to_all: bool
    cost_budget: float
    cost_budget_include_expenses: bool
    fee: float
    notes: str
    starts_on: date
    ends_on: date
    created_at: datetime
    updated_at: datetime


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
    user: object
    user_assignment: object
    client: object
    project: object
    task: object
    task_assignment: object
    external_reference: object
    invoice: object
    hours: float
    hours_without_timer: float
    rounded_hours: float
    notes: str
    is_locked: float
    locked_reason: str
    is_closed: float
    is_billed: float
    timer_started_at: datetime
    started_time: time
    ended_time: time
    is_running: float
    billable: float
    budgeted: float
    billable_rate: float
    cost_rate: float
    created_at: datetime
    updated_at: datetime
