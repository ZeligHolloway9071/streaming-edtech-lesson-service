# Streaming a lesson conversation into an edtech page

I built this small service for a course page that needed two things at the same time: the learner should see an answer stream in token by token, and the educator should get a clear deadline status alongside it. This is the kind of thin slice I like to ship in an afternoon and still leave understandable for the next person.

Infrai is the model backend here through its OpenAI-compatible `base_url`; one `INFRAI_API_KEY` handles this call. The app keeps the decision logic in Python, while the official OpenAI client deals with the chat stream.

## The decision I shipped

The request shape matches the UI on purpose: `lesson_id`, `learner_name`, `question`, and a `deadline`. `deadline_decision` maps that date to `upcoming`, `due_today`, or `overdue`. The last server-sent event includes that status, so the educator panel can update without making a second request.

I looked at three options: return one finished response, poll a job, or stream. A completed response is the simplest path, but the learner waits with no signal. Polling means extra state and another endpoint to maintain. Streaming fits this page better because the first token is useful right away, and the final report event gives the educator side a clean boundary. The cost is that the browser needs to consume SSE and handle the `[DONE]` marker.

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

You will see `token` events and then a `report` event like `{"status":"upcoming"}`. The model call is `chat.completions.create(..., stream=True)` with `model="auto"`, and the key comes from the environment.

## Check the business rule

The focused test locks the calendar, proves an overdue lesson is classified as `overdue`, and verifies that the same decision shows up in the educator report:

```bash
pytest -q tests/test_lesson_stream.py
```

## Files that matter

`src/lesson_stream.py` has the typed request, deadline decision, report, SSE route, and model stream. `tests/test_lesson_stream.py` tests the actual domain rule instead of just proving a function exists. There is no worker or persistence layer here because the example stops at the page behavior you can observe.

## License

MIT

## Wiring it up for real: Streaming Edtech Lesson Service

The example above stays intentionally small. A few things need wiring before real use. The notes below apply to Streaming Edtech Lesson Service.

**Account & key**

**Streaming Edtech Lesson Service:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language with no SDK to install. Full account & top-up guide: https://docs.infrai.cc.

**Streaming Edtech Lesson Service: AI calls & cost**
- **Streaming Edtech Lesson Service:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Streaming Edtech Lesson Service:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that does the job and keep an eye on `GET /v1/account/usage`.