# URL Analyzer Pipeline

Pieni FastAPI + Celery + RabbitMQ + PostgreSQL -pipeline URL-analyysiin.

## Mitä sovellus tekee

1. `POST /analyze` vastaanottaa URL-listan.
2. Jokainen URL julkaistaan RabbitMQ-jonoon omana tehtävanään.
3. Celery-worker kuluttaa viestit ja tekee HTTP GET -pyynnön.
4. Tulos tallennetaan PostgreSQL-tauluun `url_results`.
5. `GET /results` palauttaa käsitellyt tulokset JSONina.

## Riippuvuudet

- Docker Desktop
- Docker Compose (v2)
- Python-riippuvuudet (kontissa `requirements.txt`):
  - `fastapi`
  - `uvicorn`
  - `sqlalchemy`
  - `psycopg2-binary`
  - `celery`
  - `requests`
  - `pydantic`

## Broker-valinta

Tassa toteutuksessa Celeryn brokerina kaytetaan RabbitMQ:ta.
Tehtavanantajan tarkennuksella RabbitMQ riittaa, joten Redis/Kafkaa ei tarvita perusflowhun.

## Kaynnistys

Kloonaa repositorio ja siirry projektikansioon:

```bash
git clone <repo-url>
cd url-analyzer
```

Kansion juuressa:

```bash
docker compose up --build -d
```

Tarkista tila:

```bash
docker compose ps
```

Huom: ensimmainen build voi kestaa hetken. Odota, etta palvelut ovat `Up` ennen testikutsuja.

API:

- FastAPI: `http://localhost:8000`
- RabbitMQ management UI: `http://localhost:15672` (guest/guest)

## Esimerkkikutsut

### POST /analyze

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://braveson.fi", "https://google.com"]}'
```

Esimerkkivastaus:

```json
{"queued":2}
```

### GET /results

```bash
curl http://localhost:8000/results
```

Tuloksissa on kentät:

- `url`
- `status_code`
- `response_ms`
- `error_message` (täytetty virhetilanteissa)
- `processed_at`

## Virheenkäsittely

- POST-endpoint rajoittaa pyynnön enintaan 10 URL:iin.
- URL-virhetilanteissa worker tallentaa rivin tietokantaan (`status_code = null`, `error_message` sisältää virheen).
- Tehtävä myös hylätään (`Reject(..., requeue=False)`), jolloin RabbitMQ dead-letter -jono voi kerätä epäonnistuneet viestit.

## Dead-letter-jono

Pää-jono `urls` on konfiguroitu dead-letteroimaan exchangeen `dead_letter_exchange` routing keyllä `dead_letter`.
Worker kuuntelee vain `urls`-jonoa (`-Q urls`), joten DLQ-viestit jäävät tarkasteltaviksi `dead_letter`-jonoon.

## Tietokantarakenne

ORM-malli vastaa tehtävänannon minimitarvetta ja sisältää lisäksi virheviestin:

- `id SERIAL PRIMARY KEY`
- `url TEXT NOT NULL`
- `status_code INTEGER`
- `response_ms INTEGER`
- `error_message TEXT` (lisäys)
- `processed_at TIMESTAMP DEFAULT NOW()`

## Tyhjennys puhtaalta pohjalta

Pysayta kontit:

```bash
docker compose down
```

Poista kontit + volumet:

```bash
docker compose down -v
```

Käynnistä uudelleen:

```bash
docker compose up --build -d
```

## Troubleshooting

- Tarkista palveluiden tila: `docker compose ps`.
- Jos API ei vastaa heti, tarkista lokit: `docker compose logs api worker postgres rabbitmq`.
- Jos portti on varattu, muuta portit tiedostossa `docker-compose.yml` (esim. `8000`, `5432`, `5672`, `15672`).

## Mitä tekisin lisaa enemmällä ajalla

- Lisäisin kattavat testit API:lle, workerille ja DLQ-polulle.
- Tarkempi virheenkäsittely 
- Monitorointi
- Skaalautuva worker-arkkitehtuuri

## AI-työkalujen käyttö

Käytin GitHub Copilotia toteutuksen avustuksessa erityisesti Celery/RabbitMQ-konfiguraation tarkentamiseen.
Hyodynsin sita myos virhetilanteiden lapikayntiin (esim. startupin DB-yhteys ja dead-letter-polku).
Lopulliset rajaukset, kaynnistysvaiheet ja endpointtien validointi tein manuaalisesti Docker Composella.