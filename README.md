# URL Analyzer Pipeline

FastAPI + Celery + RabbitMQ + PostgreSQL -pipeline URL-analyysiin.

## Mitä sovellus tekee

1. `POST /analyze` vastaanottaa URL-listan.
2. Jokainen URL julkaistaan RabbitMQ:hun omana viestinään.
3. Celery-worker hakee URL:n (`HTTP GET`).
4. Tulos tallennetaan PostgreSQL-tauluun `url_results`.
5. `GET /results` palauttaa käsitellyt tulokset.

## Käynnistys

Vaatimukset: Docker Desktop + Docker Compose (v2). 
Python riippuvuudet: requirements.txt (ladataan automaattisesti docker compose up --buildissä)

```bash
git clone https://github.com/Jouni031002/Pipeline-harjoitustehtava
cd Pipeline-harjoitustehtava
```

Luo projektin juureen `.env`:

```env
POSTGRES_PASSWORD=postgres
```

Käynnistä palvelut:

```bash
docker compose up --build -d
docker compose ps
```

API: `http://localhost:8000`
RabbitMQ Management UI: `http://localhost:15672` login: guest/guest
RabbitMQ broker URL (Celery): `amqp://guest:guest@localhost:5672//`

Tietokannan nollaus: 

```bash
docker compose down -v
```

## Esimerkkikutsut

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://braveson.fi", "https://example.com"]}'
```

```json
{"queued":2}
```

```bash
curl http://localhost:8000/results
```

`GET /results` palauttaa kentät: `id`, `url`, `status_code`, `response_ms`, `error_message`, `processed_at`.

## Virheenkäsittely

- `POST /analyze` hyväksyy enintään 10 URL:ia per pyyntö.
- Virheellinen/epäonnistunut URL tallennetaan tietokantaan (`status_code = null`, `error_message` asetettu).
- Epäonnistunut tehtävä hylätään `Reject(..., requeue=False)`, jolloin RabbitMQ:n dead-letter-jono voi kerätä viestin.

## Mitä tekisin lisää enemmällä ajalla

- Lisäisin kattavat testit (unit + integraatio) API:lle, workerille ja DLQ-polulle.
- Tarkempi virheenkäsittely, esimerkiksi käsittelemällä erilaisia HTTP-virheitä ja timeout-tilanteita tarkemmin.
- Lisäisin parempaa lokitusta ja monitorointia, jotta olisi helpompi nähdä mitä pipeline tekee ja jos jokin menee pieleen.
- Skaalautuva worker-arkkitehtuuri: useampia worker-prosesseja tai -kontteja, jolloin useampia URL voidaan käsitellä samanaikaisesti.
