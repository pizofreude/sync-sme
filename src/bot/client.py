"""Discord client bootstrap helpers."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Callable

from dotenv import load_dotenv

from bot.handlers import build_message_handler
from db.models import SQLiteStateStore
from integrations.plane import PlaneCLI
from llm.parser import TaskParser
from llm.router import NineRouterClient

try:
    import discord
except ImportError:  # pragma: no cover - exercised only in runtime environments without discord.py
    discord = None


@dataclass(slots=True)
class BotSettings:
    discord_bot_token: str
    ninerouter_api_key: str
    plane_workspace_slug: str
    action_items_channel: str = "action-items"
    llm_model: str = "nvidia/llama-3.1-70b-instruct"
    state_db_path: str = "sync_sme.db"
    plane_assignee_map: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "BotSettings":
        load_dotenv()
        raw_assignee_map = os.getenv("PLANE_ASSIGNEE_MAP", "")
        assignee_map = {}
        for item in filter(None, (entry.strip() for entry in raw_assignee_map.split(","))):
            if ":" not in item:
                continue  # skip malformed entries instead of crashing
            discord_id, plane_member = item.split(":", 1)
            assignee_map[discord_id.strip()] = plane_member.strip()
        return cls(
            discord_bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
            ninerouter_api_key=os.getenv("NINEROUTER_API_KEY", ""),
            plane_workspace_slug=os.getenv("PLANE_WORKSPACE_SLUG", ""),
            action_items_channel=os.getenv("ACTION_ITEMS_CHANNEL", "action-items"),
            llm_model=os.getenv("LLM_MODEL", "nvidia/llama-3.1-70b-instruct"),
            state_db_path=os.getenv("SYNC_SME_DB_PATH", "sync_sme.db"),
            plane_assignee_map=assignee_map,
        )


def create_client(settings: BotSettings):
    if discord is None:  # pragma: no cover - depends on optional runtime dependency
        raise RuntimeError("discord.py must be installed to create the Discord client")

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    router = NineRouterClient(api_key=settings.ninerouter_api_key, model=settings.llm_model)
    parser = TaskParser(router=router)
    plane = PlaneCLI(
        workspace_slug=settings.plane_workspace_slug,
        assignee_map=settings.plane_assignee_map,
    )
    state_store = SQLiteStateStore(settings.state_db_path)
    on_message = build_message_handler(
        task_parser=parser,
        plane_client=plane,
        state_store=state_store,
        action_items_channel=settings.action_items_channel,
    )

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")

    @client.event
    async def on_message(message):
        await on_message(message)

    return client


def run() -> None:
    settings = BotSettings.from_env()
    if not settings.discord_bot_token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required")
    client = create_client(settings)
    client.run(settings.discord_bot_token)


if __name__ == "__main__":  # pragma: no cover
    run()
