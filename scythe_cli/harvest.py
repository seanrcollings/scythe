import typing as t
import httpx


class AsyncHarvest:
    def __init__(self, token: str, account_id: str):
        self.token = token
        self.account_id = account_id

        self.client = httpx.AsyncClient(
            base_url=f"https://api.harvestapp.com/api/v2/",
            headers={
                "Harvest-Account-Id": account_id,
                "Authorization": f"Bearer {token}",
            },
        )

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.__aexit__(exc_type, exc_value, traceback)

    async def close(self):
        await self.client.aclose()

    async def get_time_entries(
        self, params: t.Mapping[str, str] | None = None
    ) -> t.Mapping[str, t.Any]:
        response = await self.client.get(
            "time_entries",
            params=params,
        )
        return response.json()

    async def get_time_entry(self, id: int) -> t.Mapping[str, t.Any]:
        response = await self.client.get(f"time_entries/{id}")
        return response.json()
