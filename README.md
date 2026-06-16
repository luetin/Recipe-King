# RecipeKing

Ett receptbibliotek du kan köra på din egen Debian-server. Logga in, lägg till
recept manuellt, importera från PDF/textfil, eller skrapa recept direkt från
stödda receptsajter. Recept är delade mellan alla inloggade användare, men
bara ägaren kan redigera eller radera sina egna recept.

## Funktioner

- Inloggning med flera användarkonton (delad receptlåda)
- Skapa recept manuellt med formulär, inklusive bild
- Importera recept från PDF eller textfil (heuristisk tolkning)
- Importera recept från URL (ICA.se och Köket.se stöds via schema.org/Recipe
  JSON-LD)
- Ingredienser och instruktioner kan delas in i kategorier (t.ex. "Sås",
  "Tartarsås") — upptäcks automatiskt vid import, eller skrivs manuellt genom
  att avsluta en rad med `:`
- Taggar (t.ex. "middag", "fisk") som går att lägga till/ta bort efter att
  receptet skapats
- Sökning på titel, beskrivning och taggar
- Betygsättning 1–5 per användare, med snittbetyg
- Egna anteckningar per recept
- Tidsstämplar för skapat/senast ändrat
- Backup och återställning av databasen via skript

## Tech-stack

- **Backend**: FastAPI (Python), server-renderat med Jinja2 + HTMX
- **Databas**: PostgreSQL, SQLAlchemy + Alembic för migrationer
- **Deployment**: Docker + docker-compose

## Köra lokalt (utveckling, utan Docker)

Kräver Python 3.12+.

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows
# eller: source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt

# SQLite duger fint för lokal utveckling
export SECRET_KEY=dev-secret-key
export DATABASE_URL=sqlite:///./dev.db
export UPLOAD_DIR=./uploads

python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8001
```

Öppna sedan http://localhost:8001.

## Köra med Docker (produktion på Debian)

1. Installera Docker Engine och Compose-plugin på servern.
2. Kopiera `.env.example` till `.env` och fyll i en riktig `SECRET_KEY` samt
   ett eget Postgres-lösenord:
   ```bash
   cp .env.example .env
   ```
3. Bygg och starta:
   ```bash
   docker compose up -d --build
   ```
   Databasmigrationer körs automatiskt vid uppstart
   ([docker-entrypoint.sh](docker-entrypoint.sh)).
4. Sätt en reverse proxy (t.ex. Caddy) framför port 8000 för HTTPS.

Uppladdade bilder lagras under `./uploads` (volymmonterad), så de överlever
omstarter och omdeployer.

## Backup och återställning

```bash
# Ta en backup (sparas i backups/ med tidsstämpel)
./scripts/backup.sh

# Återställ från en backup (skriver över all nuvarande data, kräver bekräftelse)
./scripts/restore.sh backups/recipeking_20260101_120000.sql
```

## Projektstruktur

```
app/
├── main.py              # FastAPI-app, routning, felhantering
├── models.py            # SQLAlchemy-modeller
├── routers/             # auth, recipes, upload, scrape
├── services/            # affärslogik: recipe_service, file_import, image_service
├── scraping/            # JSON-LD-baserad receptscraping
├── templates/           # Jinja2-mallar
└── static/              # CSS/JS

migrations/              # Alembic-migrationer
scripts/                 # backup.sh, restore.sh
```

## Stödda receptsajter för URL-import

- ICA.se
- Köket.se (recept.nu omdirigerar hit)

Fler sajter kan läggas till i [app/scraping/registry.py](app/scraping/registry.py),
förutsatt att sajten embeddar schema.org/Recipe JSON-LD i sin HTML.
