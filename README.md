# MATHutrice

MATHutrice is an educational tutor powered by an LLM designed to support first-year students in learning mathematical tools. 

To provide an optimal learning experience, the application offers a clear and intuitive interface where students can:
- Benefit from simple and structured navigation.
- Gain visibility on their progression (both globally and by specific subthemes).
- Quickly access practice sessions (e.g., via the "M'entraîner" button on module pages like Trigonometry).
- Track evaluated skills based on EPF/Moodle standards.

*Visual mockup for the home page:*
<img width="934" height="522" alt="image" src="https://github.com/user-attachments/assets/faa9c372-129c-4414-9160-f5f263b10f12" />

---

## Running locally

Requires [uv](https://docs.astral.sh/uv/). It installs the Python version in `.python-version` and the dependency versions in `uv.lock`.

```sh
git clone -b course-2026 <your fork URL> mathutrice
cd mathutrice
uv sync
cp .env.example .env      # then set LLM_API_KEY in .env
uv run python -m mathutrice.fonctions_python.seed   # notions and competences
uv run uvicorn mathutrice.app:app --port 8000
```

Then open <http://localhost:8000/>. To check that everything works, follow [docs/smoke-test.md](docs/smoke-test.md).

### Environment variables

`.env.example` lists every setting with its default; `.env` is git-ignored, so a key never reaches a commit.

- `LLM_API_KEY` (required): key for the LLM endpoint. The default endpoint is Mistral (<https://console.mistral.ai>, a free account works). The application refuses to start without it.
- `LLM_BASE_URL`, `LLM_MODEL`: the OpenAI-compatible endpoint and its model.
- `DATABASE_URL`: SQLite file by default (`sqlite:///./mathutrice.db`), created in the directory you start from.
- `SESSION_SECRET` (required): signs session cookies.
- `AUTH_MODE`: `dev` (default in `.env.example`) or `entra`. When unset, it defaults to `entra`.

### Seeding the database

Modules and training need the notions and competences of the referentiel in the database. The seed script creates them from `mathutrice/referentiel.py`, and can be re-run safely:

```sh
uv run python -m mathutrice.fonctions_python.seed
```

### Architecture check

Package boundaries are enforced; see [mathutrice/README.md](mathutrice/README.md).

```sh
uv run tach check
uv run python scripts/check_cycles.py
```

## Development sign-in (forks and non-Entra environments)

With `AUTH_MODE=dev`, `/dev/login` signs you in as any `@epfedu.fr` address and role (Student, Teacher or Admin), with no proof of identity. Never use it in production.

- `DEV_LOGIN_KEY`: optional shared key protecting the sign-in page. Empty means no key.
- `SESSION_SECRET`: if it keeps the placeholder value of `.env.example`, anyone can forge a session cookie, so replace it with a random secret on any deployed environment.
- `REDIRECT_URL`, `POST_LOGOUT_REDIRECT_URL`: only used with `AUTH_MODE=entra`.

### Scripted sign-in (curl)

```sh
# Sign in and save the session cookie
curl -c cookie.txt -d "email=student@epfedu.fr" -d "role=Student" -d "key=YOUR_DEV_LOGIN_KEY"      http://localhost:8000/dev/login

# Use it on later requests
curl -b cookie.txt http://localhost:8000/
```
