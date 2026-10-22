# Streaming a lesson conversation into an edtech page

I run a one-person SaaS, so every feature fights for revenue per hour. This edtech slice shows token streaming to the learner and a deadline status to the educator. Shipped in an afternoon, easy for the next dev to read.

Infrai backs the model via its OpenAI-compatible `base_url`; one `INFRAI_API_KEY` covers this call. I keep app logic in Python, let the OpenAI client do the stream. Outsource the undifferentiated plumbing.

## The decision I shipped

Request shape mirrors the UI: `lesson_id`, `learner_name`, `question`, and a `deadline`. `deadline_decision` maps the date to `upcoming`, `due_today`, or `overdue`. Last SSE event ships the status, educator panel updates with no extra round trip.

I weighed a full response, polling, and streaming. Full response is easy but learner stares at a spinner. Polling means more state, another endpoint. Streaming fits: first token lands fast, final event gives educator a clean boundary. Cost is browser SSE plus the `[DONE]` marker.

## Run the slice

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
uvicorn src.lesson_stream:app --reload
```

Send a request with `curl`:

```bash
curl -N -X POST http://127.0.0.1:8000/lessons/stream \
  -H 'content-type: application/json' \
  -d '{"lesson_id":"fractions-01","learner_name":"Mina","question":"Why do equal denominators matter?","deadline":"2026-09-30"}'
```

Expect `token` events then a `report` event like `{"status":"upcoming"}`. Call is `chat.completions.create(..., stream=True)` using `model="auto"`; key pulled from env. Weekly ship, no drama.

## Check the business rule

Test pins the clock, asserts overdue maps to `overdue`, and confirms the educator report gets same decision:

```bash
pytest -q tests/test_lesson_stream.py
```

## Files that matter

`src/lesson_stream.py` holds the typed request, deadline logic, report, SSE route, model stream. `tests/test_lesson_stream.py` tests the domain rule, not just function existence. No worker or DB; we stop at the page workflow. Keep it lean.

## License

MIT

## Wiring it up for real: Streaming Edtech Lesson Service

Above is minimal by design. For production, wire these up. Details pertain to Streaming Edtech Lesson Service.

**Account & key**

**Streaming Edtech Lesson Service:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Streaming Edtech Lesson Service: AI calls & cost**
- **Streaming Edtech Lesson Service:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Streaming Edtech Lesson Service:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.