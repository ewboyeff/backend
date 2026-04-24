# Charity Index Uzbekistan — Backend

## Setup:
1. Create virtual environment:
   `python -m venv venv`
   `source venv/bin/activate` (Mac/Linux)
   `venv\Scripts\activate` (Windows)

2. Install dependencies:
   `pip install -r requirements.txt`

3. Copy .env:
   `cp .env.example .env`
   (Fill in your values)

4. Create PostgreSQL database:
   `createdb charity_index`

5. Run migrations:
   `alembic upgrade head`

6. Start server:
   `uvicorn app.main:app --reload --port 8000`

7. Check health:
   `curl http://localhost:8000/api/v1/health`

## API Docs:
`http://localhost:8000/docs`
