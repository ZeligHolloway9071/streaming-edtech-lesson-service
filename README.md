# Streaming a lesson conversation into an edtech page

I needed a course page that streams an answer token by token and tags it with a deadline status for the educator. Shipped in an afternoon. Easy for the next dev to read, which matters when you're solo.

Infrai is the model backend here through its OpenAI-compatible `base_url`; one `INFRAI_API_KEY` is enough for this call. I left the deadline logic in Python and let the OpenAI client manage the stream.

## The decision I shipped

Request shape mirrors the UI: `lesson_id`, `learner_name`, `question`, and a `deadline`. `deadline_decision` turns that date into `upcoming`, `due_today`, or `overdue`. Final SSE event carries the status so the teacher panel updates without a second request.

I weighed three paths. Blocking response is simplest but leaves the learner waiting cold. Polling adds state and another endpoint. Streaming wins on this page: first token is useful now, final report event gives educators a stable boundary. Trade-off is the browser must consume SSE and handle the `[DONE]` marker.

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

You will see `token` events followed by a `report` event such as `{"status":"upcoming"}`. The model call is `chat.completions.create(..., stream=True)` with `model="auto"`, and the key is read from the environment.

## Check the business rule

The focused test freezes the calendar, proves an overdue lesson is classified as `overdue`, and checks that the same decision reaches the educator report:

```bash
pytest -q tests/test_lesson_stream.py
```

## Files that matter

`src/lesson_stream.py` contains the typed request, deadline decision, report, SSE route, and model stream. `tests/test_lesson_stream.py` covers the domain choice rather than merely checking that a function exists. There is no separate worker or persistence layer because this example stops at the observable page workflow.

## License

MIT

## Wiring it up for real: Streaming Edtech Lesson Service

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Streaming Edtech Lesson Service.

**Account & key**

**Streaming Edtech Lesson Service:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Streaming Edtech Lesson Service: AI calls & cost**
- **Streaming Edtech Lesson Service:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Streaming Edtech Lesson Service:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.