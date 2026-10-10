from datetime import date
from types import SimpleNamespace

from src import lesson_stream
from src.lesson_stream import LessonRequest, build_report, deadline_decision


def test_deadline_decision_drives_educator_report():
    request = LessonRequest(
        lesson_id="fractions-01",
        learner_name="Mina",
        question="Why do equal denominators matter?",
        deadline=date(2026, 9, 9),
    )

    assert deadline_decision(request.deadline, date(2026, 9, 10)).status == "overdue"
    assert build_report(request, date(2026, 9, 10)).deadline_status == "overdue"


def test_stream_skips_empty_choice_chunks(monkeypatch):
    request = LessonRequest(
        lesson_id="fractions-01",
        learner_name="Mina",
        question="Why do equal denominators matter?",
        deadline=date(2026, 9, 9),
    )
    chunks = [
        SimpleNamespace(choices=[]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="They align parts."))]),
        SimpleNamespace(choices=[]),
    ]
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: iter(chunks)))
    )
    monkeypatch.setattr(lesson_stream, "_client", lambda: client)

    events = list(lesson_stream.stream_answer(request))

    assert '"type": "token", "text": "They align parts."' in events[0]
    assert '"type": "report"' in events[1]
    assert events[2] == "data: [DONE]\n\n"
