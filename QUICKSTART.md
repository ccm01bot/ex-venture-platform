# Quick Start Guide for EX Venture Platform

## One-Command Setup (with Docker)

```bash
chmod +x start.sh
./start.sh
```

This will:
1. Build Docker images for backend, frontend, and services
2. Start PostgreSQL, Redis, and the application
3. Run database migrations
4. Access at:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Manual Setup (without Docker)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
# 1. Create database in PostgreSQL
#    createdb ex_venture
# 2. Run migrations
#    alembic upgrade head

# Start server
python main.py
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Celery Worker (optional, for async tasks)

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

## First Steps After Startup

1. **Register Account**
   - Go to http://localhost:3000/login
   - Click "Sign up"
   - Create account with email and password

2. **Add Your First Company**
   - Navigate to "Companies"
   - Click "+ Add Company"
   - Enter company name and website URL
   - Add industry tags (optional)

3. **Run a Scan**
   - Go to "Dashboard" or "Scan All"
   - Click "Scan All Companies"
   - Wait for results

4. **Generate Content**
   - Select a company
   - Go to "Content Creator" tab
   - Choose platform, tone, and topic
   - Click "Generate Article Content"

## Environment Variables

### Backend (.env)
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `REDIS_URL` - Redis connection string
- `ANTHROPIC_API_KEY` - Claude API key (optional but needed for AI features)
- `OPENAI_API_KEY` - OpenAI API key (optional but needed for images)
- `RESEND_API_KEY` - Email service API key (optional)

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)

## Common Commands

### Backend
```bash
cd backend

# Run tests
pytest

# Format code
black . && isort .

# Type checking
mypy .

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

### Frontend
```bash
cd frontend

# Format code
npm run format

# Lint
npm run lint

# Type check
npm run type-check

# Build for production
npm run build
```

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port
# macOS/Linux:
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Database Connection Error
```bash
# Check PostgreSQL
psql -U user -d ex_venture

# Reset database
dropdb ex_venture
createdb ex_venture
alembic upgrade head
```

### Redis Connection Error
```bash
# Check Redis
redis-cli ping

# Start Redis service (if not running)
redis-server
```

### Module Not Found (Backend)
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Module Not Found (Frontend)
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Architecture Overview

```
┌─────────────────────────┐
│     Next.js Frontend    │
│  (React + Tailwind)     │
│   Port: 3000            │
└────────────┬────────────┘
             │ API Calls
┌────────────▼────────────┐
│   FastAPI Backend       │
│  (Python + SQLAlchemy)  │
│   Port: 8000            │
└────┬───────────┬────────┘
     │           │
┌────▼──┐    ┌───▼─────┐
│  PG   │    │  Redis  │
│(Data) │    │(Cache)  │
└───────┘    └─────────┘
     │           │
┌────▼───────────▼───────┐
│  Celery Tasks Queue    │
│  (Async Processing)    │
└────────────────────────┘
```

## Next Steps

1. **Customize Styling** - Update `frontend/tailwind.config.ts`
2. **Add Your API Keys** - Set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
3. **Connect Integrations** - YouTube, Google Search Console, etc.
4. **Deploy** - Use Railway, Vercel, or your preferred platform
5. **Add Webhooks** - For tracking content performance

## Support & Resources

- Architecture Plan: See `EX_Venture_Platform_Architecture_Plan.md`
- FastAPI Docs: https://fastapi.tiangolo.com
- Next.js Docs: https://nextjs.org/docs
- SQLAlchemy Guide: https://docs.sqlalchemy.org
- PostgreSQL Docs: https://www.postgresql.org/docs

## Stopping Services

```bash
# Using Docker
./stop.sh

# Manual cleanup (if running locally)
# Kill backend: Ctrl+C
# Kill frontend: Ctrl+C
# Kill Celery: Ctrl+C
```
