# Независимый судья / Independent Judge

Оригинал + два перевода одного фрагмента → сравнение → количество и типы
кандидатов на исправление, цитаты, обоснования и научный аппарат.

Основной сценарий на русском: **Готовый пример** или **Свои материалы**.
Оценивается количество оставшихся необходимых правок. Сохранённые машинные
находки и спорные замечания отделены от подтверждённых человеком исправлений.
Подтверждённое число правок в нынешнем пилоте **не установлено**.

Генерация научного аппарата показана как самостоятельная возможность Kitabs:
в сохранённом результате — 25 примечаний к хадисам, 19 справочных записей о
персоналиях и 13 словарных статей, с проверяемыми примерами. Эти записи
демонстрируют уже выполненную платформой работу; точность содержания и
необходимые дополнения оцениваются отдельно.

Таймер и ручное создание заданий не входят в основной сценарий. Старый
редакторский экран, его API и данные сохранены по `/editorial`.
[Предыдущий README](docs/readme-editorial-history-2026-10-04.md) — история этапа.

## Локальный запуск

Из корня этого отдельного репозитория, Python 3.12+:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps -e backend
JUDGE_DATA_DIR="$PWD/.judge-data/editorial-stand-2026-10-04" .venv/bin/python -m uvicorn independent_judge.api.app:create_app --factory --host 127.0.0.1 --port 8766
```

В другом терминале, Node.js 22+:

```sh
cd frontend
npm ci --ignore-scripts
NEXT_TELEMETRY_DISABLED=1 JUDGE_API_ORIGIN=http://127.0.0.1:8766 npm run build
NEXT_TELEMETRY_DISABLED=1 npm start
```

Откройте <http://127.0.0.1:3005>. `JUDGE_API_ORIGIN` задаётся при сборке.
`GET /health`: `stage: comparison`, `live_enabled: false`.

Новый экран не делает LLM-запросов. Он открывает сохранённые результаты и
принимает TXT, MD, DOCX, текстовый PDF либо вставленный текст. После предпросмотра
нужно подтвердить совпадение смысловых границ. Автоматической обрезки нет.
Если сохранённый результат точно совпадает по трём текстам, языкам и профилю,
он переиспользуется. Иначе выводится «количество правок пока неизвестно».
Для возвращения к загруженным материалам сохраните адрес страницы с `#scope=`.

Реальный корпус и отчёты находятся в приватном `JUDGE_DATA_DIR/comparison-catalog`,
исключённом из Git. В чистом клоне каталог пуст: материалы не публикуются вместе
с кодом. Русская инструкция и паспорт: [comparison-guide-ru.md](docs/comparison-guide-ru.md).
Стенд слушает только loopback. Публичный доступ жюри, аутентификация, лицензии
корпуса и конкурсный релиз пока не подготовлены.

## Try three documents

```sh
curl --fail-with-body http://127.0.0.1:8765/api/comparisons \
  -F 'source=@original.txt' \
  -F 'a=@version-a.txt' \
  -F 'b=@version-b.txt' \
  -F 'source_language=ar' \
  -F 'target_language=en'
```

The response contains an ID, `draft` status and extracted text for each role.
Retrieve it with `GET /api/comparisons/{id}`. Pasted text uses
`POST /api/comparisons/text` with JSON fields `source`, `a`, `b`,
`source_language` and `target_language`.

Supported inputs: UTF-8 TXT/MD, DOCX and PDF with a selectable text layer.
Each input is limited to 20 MiB; the entire HTTP request is limited to 61 MiB.
No OCR, translation or external network request is triggered by upload.

Always inspect the extracted text. PDF layout/reading order can differ from the
page. A PDF page without text requires manual review; even an intentionally blank
page needs handling before this version accepts the PDF. DOCX paragraphs, table
paragraphs, footnotes and endnotes are supported; headers, footers, comments and
text inside images are excluded and reported as extraction warnings. Resolve
tracked text revisions before uploading DOCX. Expanded DOCX size is limited to
80 MiB.

## Verify

```sh
.venv/bin/python -m pytest -q
npm --prefix frontend test
npm --prefix frontend run typecheck
NEXT_TELEMETRY_DISABLED=1 npm --prefix frontend run build
git diff --check
```

The tests cover persistence across restarts, original byte/text hashes, parser
errors, size limits, notes, missing PDF text pages and intake with outbound
connections disabled. Test fixtures are engineering controls, not a showcase
or evidence of translation quality.

See [architecture](docs/architecture.md), [baseline](BASELINE.md) and the
[intake verification](docs/intake-verification-2026-10-04.md) and
[editorial verification](docs/editorial-verification-2026-10-04.md).

## Bounded evaluation pilot

Create a confirmed scope with `POST /api/comparisons/{id}/scopes` (see
[scope contract](docs/scope-verification-2026-10-04.md)). Offsets are Unicode code
points, not UTF-16 browser offsets. Each range includes the entire input text hash.
Check the three previews before setting `confirmed: true`.

```sh
.venv/bin/python -m independent_judge.cli --scope-id SCOPE_ID --run-id UNIQUE_RUN_ID
```

This preflight makes no model call. To run, supply `AI_GATEWAY_API_KEY`,
`JUDGE_BUDGET_TOTAL_USD` and `JUDGE_BUDGET_RUN_USD` securely in the process environment,
then add `--live`. An explicit example budget is total `3`, per-run `1` USD.
`--translator-a-vendor` / `--translator-b-vendor` record known model families;
omitted provenance remains unknown. Use the same data directory for all budgeted
runs. Changing the data directory creates a different ledger; this operator CLI
is not a multi-tenant billing boundary.

Live runs require a clean committed checkout. Failed/uncertain calls are not
silently retried; unresolved cost reservations stay held. Duplicate run IDs cannot
trigger another request. Reports and raw receipts stay in the private data
folder, never Git. An incomplete run has no final scores. See
[protocol and limitations](docs/evaluation-protocol.md).

A [real Sonnet 5.5 pilot](docs/sonnet-pilot-2026-10-04.md) completed on 4 October: 15 calls in the full protocol, status `needs_review`. All attempts cost $0.313172. Findings require review; this is not a validated platform ranking.
