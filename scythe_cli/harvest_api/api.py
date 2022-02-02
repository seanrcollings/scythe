import logging
import typing as t

import requests
from . import schemas

logger = logging.getLogger("arc_logger")


class RequestError(Exception):
    def __init__(self, response: requests.Response):
        self.response = response

    def __str__(self):
        try:
            return self.response.json()["message"]
        except:
            return "No error message found in response"

    @property
    def status_code(self) -> int:
        return self.response.status_code


class Session(requests.Session):
    def __init__(self, base_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = base_url

    def get_url(self, url: str):
        if url.startswith("http"):
            return url

        return f"{self.base_url}{url}"

    def _handle_res(self, res: requests.Response):
        if res.status_code > 299:
            raise RequestError(res)
        return res

    def get(self, url, **kwargs):
        logger.debug("Fetching %s", url)
        return self._handle_res(super().get(f"{self.get_url(url)}", **kwargs))

    def post(self, url, data=None, json=None, **kwargs):
        logger.debug("Posting %s", url)
        return self._handle_res(
            super().post(f"{self.get_url(url)}", data, json, **kwargs)
        )

    def put(self, url, data=None, **kwargs):
        return self._handle_res(super().put(f"{self.get_url(url)}", data, **kwargs))

    def patch(self, url, data=None, **kwargs):
        return self._handle_res(super().patch(f"{self.get_url(url)}", data, **kwargs))

    def delete(self, url, *args, **kwargs):
        logger.debug("Deleting %s", url)
        return self._handle_res(super().delete(f"{self.get_url(url)}", *args, **kwargs))


T = t.TypeVar("T")
P = t.TypeVar("P")


class RecordCollection(t.Generic[T]):
    def __init__(
        self,
        values: t.Sequence[T],
        pagination_key: str,
        session: Session,
        page: int,
        total_pages: int,
        total_entries: int,
        links: dict,
        previous_page: int = None,
        next_page: int = None,
    ):
        self._values = values
        self._session = session
        self._schema = type(self._values[0]) if self._values else None
        self._pagination_key = pagination_key
        self.page = page
        self.total_pages = total_pages
        self.total_entries = total_entries
        self.next_page = next_page
        self.previous_page = previous_page
        self.links = links

    def __repr__(self) -> str:
        return f"RecordCollection({self._values!r})"

    def __getitem__(self, index: int) -> T:
        return self._values[index]

    def __len__(self):
        return len(self._values)

    def __iter__(self) -> t.Generator[T, None, None]:
        yield from self._values

    def __next__(self):
        next_link = self.links.get("next")
        if next_link:
            data = self._session.get(self.links["next"]).json()
            return RecordCollection(
                values=[self._schema(**item) for item in data[self._pagination_key]],
                session=self._session,
                pagination_key=self._pagination_key,
                page=data["page"],
                total_pages=data["total_pages"],
                total_entries=data["total_entries"],
                next_page=data["next_page"],
                previous_page=data["previous_page"],
                links=data["links"],
            )
        raise StopIteration()

    def more(self) -> bool:
        return self.next_page is not None


class Record(t.Generic[T, P]):
    def __init__(
        self,
        session: Session,
        endpoint: str,
        pagination_key: str,
        schema: type[T],
    ):
        self.session = session
        self.endpoint = endpoint
        self.pagination_key = pagination_key
        self.schema = schema

    def list(self, params: t.Optional[P] = None) -> RecordCollection[T]:
        kwargs = {}
        if params:
            kwargs["params"] = params

        data = self.session.get(self.endpoint, **kwargs).json()
        return RecordCollection(
            values=[self.schema(**item) for item in data[self.pagination_key]],
            session=self.session,
            pagination_key=self.pagination_key,
            page=data["page"],
            total_pages=data["total_pages"],
            total_entries=data["total_entries"],
            next_page=data["next_page"],
            previous_page=data["previous_page"],
            links=data["links"],
        )

    def get(self, id: int, params: t.Optional[P] = None) -> T:
        kwargs = {}
        if params:
            kwargs["params"] = params
        return self.schema(**self.session.get(f"{self.endpoint}/{id}", **kwargs).json())

    def create(self, data: dict) -> T:
        return self.schema(**self.session.post(self.endpoint, json=data).json())

    def update(self, id: int, data: dict) -> T:
        return self.schema(
            **self.session.patch(f"{self.endpoint}/{id}", json=data).json()
        )

    def delete(self, id: int):
        return self.schema(**self.session.delete(f"{self.endpoint}/{id}").json())


class TimeEntryRecord(Record[schemas.TimeEntry, schemas.TimeEntryParams]):
    def running(self) -> t.Optional[schemas.TimeEntry]:
        data = self.session.get("/time_entries", params={"is_running": "true"}).json()
        if data["time_entries"]:
            return self.schema(**data["time_entries"][0])
        return None

    def restart(self, id: int) -> schemas.TimeEntry:
        return self.schema(**self.session.patch(f"/time_entries/{id}/restart").json())

    def stop(self, id: int) -> schemas.TimeEntry:
        return self.schema(**self.session.patch(f"/time_entries/{id}/stop").json())


# TODO: Integrate the cache directly into the API?


class Harvest:
    def __init__(self, token: str, account_id: t.Union[str, int]):
        super().__init__()
        self.session = Session("https://api.harvestapp.com/v2")
        self.session.headers.update(
            {
                "Harvest-Account-Id": str(account_id),
                "Authorization": f"Bearer {token}",
                "User-Agent": "Scythe CLI",
            }
        )

        self.time_entires = TimeEntryRecord(
            self.session, "/time_entries", "time_entries", schema=schemas.TimeEntry
        )
        self.project_assignments = Record[schemas.ProjectAssignment, None](
            self.session,
            "/users/me/project_assignments",
            "project_assignments",
            schema=schemas.ProjectAssignment,
        )

    def me(self) -> schemas.User:
        return schemas.User(**self.session.get("/users/me").json())

        # def me(self):

    #     return self.get("/users/me")

    # def get_projects(self) -> requests.Response:
    #     return self.get("/users/me/project_assignments")

    # def get_running_timer(self):
    #     timers = self.get("/time_entries?is_running=true").json()["time_entries"]
    #     return timers[0] if len(timers) > 0 else None

    # def create_timer(
    #     self, project_id, task_id, notes: str = "", spent_date=datetime.date.today()
    # ):
    #     return self.post(
    #         "/time_entries",
    #         {
    #             "project_id": project_id,
    #             "task_id": task_id,
    #             "spent_date": str(spent_date),
    #             "notes": notes,
    #         },
    #     )
