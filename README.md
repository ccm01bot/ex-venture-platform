# EX Venture Platform - Full Stack Application

Complete SEO & Compliance Monitor with Outreach, Financial Tracking, and AI Content Generation.

## Project Structure

```
ex-venture-platform/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── routes/          # API endpoints
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Business logic
│   │   ├── tasks/           # Celery async tasks
│   │   ├── core/            # Configuration, auth, database
│   │   └── main.py          # FastAPI app
│   ├── alembic/             # Database migrations
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Docker configuration
│   └── main.py              # Entry point

└── frontend/
    ├── app/
    │   ├── layout.tsx       # Root layout
    │   ├── page.tsx         # Home page
    │   ├── login/           # Login page
    │   ├── dashboard/       # Dashboard
    │   ├── companies/       # Companies list/management
    │   ├── scan/            # Scan all page
    │   ├── publish/         # Article management
    │   ├── export/          # Export data
    │   ├── outreach/        # Outreach campaigns
    │   ├── financial/       # Financial tracking
    │   ├── youtube-seo/     # YouTube SEO optimizer
    │   └── youtube-analytics/ # YouTube analytics
    ├── components/          # Reusable React components
    ├── lib/                 # Utilities and helpers
    ├── package.json         # Node dependencies
    ├── tailwind.config.ts   # Tailwind configuration
    └── tsconfig.json        # TypeScript configuration
```

## Technology Stack

### Backend
- **FastAPI** (Python 3.11+)
- **PostgreSQL** 15+ with SQLAlchemy 2.0 (async)
- **Alembic** for migrations
- **Celery** + **Redis** for task queue
- **JWT** authentication
- **Anthropic Claude** & **OpenAI** for AI features
- **Resend** for email

### Frontend
- **Next.js** 14 (React 18)
- **TypeScript**
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **Zustand** for state management
- **React Query** for server state

## Setup Instructions

### Backend Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Create `.env` file**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Setup PostgreSQL**:
   - Ensure PostgreSQL 15+ is running
   - Create database: `createdb ex_venture`

4. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Start services**:
   ```bash
   # Terminal 1: API server
   python main.py

   # Terminal 2: Redis (if not running as service)
   redis-server

   # Terminal 3: Celery worker
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Create `.env.local`**:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000)

## API Documentation

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Companies
- `GET /api/companies` - List companies
- `POST /api/companies` - Create company
- `GET /api/companies/{id}` - Get company detail
- `PUT /api/companies/{id}` - Update company
- `DELETE /api/companies/{id}` - Delete company

### Scanning
- `POST /api/scans/run-all` - Scan all companies
- `GET /api/scans/status` - Get scan status
- `GET /api/dashboard/stats` - Get dashboard statistics

### Content
- `GET /api/content` - List content
- `POST /api/content` - Generate content
- `GET /api/content/{id}` - Get content detail
- `POST /api/content/{id}/publish` - Publish content
- `POST /api/content/upload-photos` - Upload images

### Financial
- `GET /api/financial/accounts` - List accounts
- `POST /api/financial/accounts` - Create account
- `GET /api/financial/transactions` - List transactions
- `POST /api/financial/transactions` - Create transaction
- `GET /api/financial/summary` - Get financial summary

### Outreach
- `GET /api/outreach/campaigns` - List campaigns
- `POST /api/outreach/campaigns` - Create campaign
- `GET /api/outreach/campaigns/{id}` - Get campaign detail
- `GET /api/outreach/analytics` - Get analytics

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ex_venture
SECRET_KEY=your-secret-key-change-in-production
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
RESEND_API_KEY=your-key
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Features

### Core
- ✅ Multi-company portfolio management
- ✅ SEO scanning & scoring
- ✅ Legal compliance checking
- ✅ User authentication with JWT

### Content
- ✅ AI-powered article generation
- ✅ Multi-platform content adaptation
- ✅ Image generation with AI
- ✅ Content publishing

### YouTube
- ✅ YouTube SEO optimization
- ✅ Channel analytics
- ✅ Video metrics tracking

### Outreach
- ✅ Campaign management
- ✅ Contact CRM
- ✅ Media lists
- ✅ Press releases
- ✅ Multi-channel outreach

### Financial
- ✅ Account management
- ✅ Transaction tracking
- ✅ Financial reporting
- ✅ P&L summaries

## Development

### Backend Development
- All async operations use `AsyncSession`
- Models extend `Base` from `app.core.database`
- Routes use dependency injection for auth and DB
- Celery tasks are defined in `app/tasks/`

### Frontend Development
- All pages are in `app/` directory (Next.js 14 App Router)
- Reusable components in `components/`
- Use TypeScript for type safety
- Tailwind CSS for styling

## Deployment

### Docker
```bash
# Backend
docker build -t ex-venture-backend ./backend
docker run -p 8000:8000 ex-venture-backend

# Frontend (build first)
cd frontend && npm run build
```

### Environment-specific Config
- Development: Local `.env` files
- Production: Use environment variables
- Update `SECRET_KEY` in production

## Testing & Debugging

### Backend
- API docs at `http://localhost:8000/docs`
- ReDoc at `http://localhost:8000/redoc`
- Health check: `GET /health`

### Frontend
- React DevTools for component debugging
- Check browser console for API errors
- Use Next.js debug command: `npm run dev -- --debug`

## Next Steps

1. **Database Setup**: Execute `alembic upgrade head`
2. **API Integration**: Connect frontend forms to backend API
3. **AI Integration**: Add Anthropic/OpenAI API keys
4. **Authentication**: Complete JWT token refresh logic
5. **Testing**: Add pytest for backend, Jest for frontend
6. **Deployment**: Set up CI/CD pipeline

## Support

For issues or questions, refer to:
- Architecture Plan (EX_Venture_Platform_Architecture_Plan.md)
- FastAPI docs: https://fastapi.tiangolo.com
- Next.js docs: https://nextjs.org/docs
