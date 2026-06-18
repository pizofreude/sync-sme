from llm.parser import ParsedTask, TaskParser


class FakeRouter:
    def __init__(self, response: str):
        self.response = response

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self.response


def test_parse_response_returns_structured_task():
    task = TaskParser.parse_response(
        '{"title": "Ship demo bot", "assignee": "<@123>", "due_date": "2026-06-20", "details": "Mention in standup"}'
    )

    assert task == ParsedTask(
        title="Ship demo bot",
        assignee="<@123>",
        due_date="2026-06-20",
        details="Mention in standup",
    )


def test_parse_response_rejects_invalid_or_empty_payloads():
    assert TaskParser.parse_response("not-json") is None
    assert TaskParser.parse_response('{"title": ""}') is None


def test_parse_message_loads_prompt_and_uses_router(tmp_path):
    prompt_path = tmp_path / "parse_task.txt"
    prompt_path.write_text("system prompt", encoding="utf-8")
    parser = TaskParser(FakeRouter('{"title": "Follow up with Alex"}'), prompt_path=prompt_path)

    task = parser.parse_message("todo: follow up with Alex")

    assert task == ParsedTask(title="Follow up with Alex", assignee=None, due_date=None, details=None)
