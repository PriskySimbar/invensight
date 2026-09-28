# InvenSight AI - Smart Warehouse Analytics

Enterprise SaaS B2B application for intelligent warehouse analytics powered by AI.

## 🚀 Features

### Core Features
- **AI-Powered SQL Generation**: Self-correcting SQL agent using LangGraph + Groq LLM
- **Real-time Analytics**: Interactive chat interface for warehouse data analysis
- **Multi-Modal AI**: Text-to-SQL, RAG (document Q&A), and Vision/OCR capabilities
- **Enterprise UI**: Modern chat interface inspired by ChatGPT/Claude
- **Data Visualization**: Dynamic charts and tables using Recharts

### Advanced Features
- **Authentication**: Google OAuth via NextAuth.js
- **Caching**: Redis Cloud integration for 60%+ response time improvement
- **Rate Limiting**: Per-user rate limiting with Redis
- **AI Observability**: Langfuse integration for tracing and monitoring
- **Cost Tracking**: Token usage and API cost monitoring
- **RAG Evaluation**: DeepEval integration for response quality assessment
- **Docker Ready**: Containerized deployment for kubeletto.com

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI (Python)
- **AI Engine**: LangGraph + Groq (llama-3.3-70b-versatile)
- **Database**: Neon Serverless PostgreSQL
- **Cache**: Redis Cloud
- **ML Libraries**: LangChain, FAISS, Sentence Transformers
- **OCR**: Tesseract + Pillow

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI Library**: shadcn/ui + Tailwind CSS
- **Charts**: Recharts
- **Auth**: NextAuth.js
- **Markdown**: react-markdown + remark-gfm

## 📋 Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Google Cloud Console account (for OAuth)
- Redis Cloud account (for caching)
- Langfuse account (for AI observability)
- Groq API key (for LLM)

## 🔧 Setup Instructions

### 1. Environment Variables

Create `.env` files in both `backend/` and `frontend/`:

**Backend (.env):**
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
REDIS_URL=redis://default:your-token@host:6379
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
NEXTAUTH_URL=http://localhost:3002
NEXTAUTH_SECRET=your_nextauth_secret
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_MS=60000
COST_TRACKING_ENABLED=true
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
NEXTAUTH_URL=http://localhost:3002
NEXTAUTH_SECRET=your_nextauth_secret
```

### 2. Database Setup

Run the seed script to populate the database:
```bash
cd backend
python seed_data.py
```

This creates:
- 10 warehouses in Indonesian cities
- 100 products (Electronics & Office supplies)
- 500 inventory records
- 10,000 transaction records (2023–present)

### 3. Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 4. Docker Deployment

**Using Docker Compose:**
```bash
docker-compose up --build
```

**Individual Services:**
```bash
# Backend
docker build -t invensight-backend ./backend
docker run -p 8000:8000 invensight-backend

# Frontend
docker build -t invensight-frontend ./frontend
docker run -p 3000:3000 invensight-frontend
```

## 📊 API Endpoints

### Core Analytics
- `POST /api/v1/analyze` - AI-powered warehouse analysis
- `GET /api/v1/metrics` - Performance and cost metrics

### RAG System
- `POST /api/v1/documents/upload` - Upload PDF for document Q&A
- `POST /api/v1/rag/query` - Query uploaded documents

### Vision/OCR
- `POST /api/v1/vision/analyze` - Analyze inventory images

### Health
- `GET /health` - Health check

## 🎯 Usage Examples

### Text-to-SQL Analysis
```
Question: "Show me the top 5 products by stock level"
Response: SQL query + data + summary + chart
```

### Document Q&A (RAG)
```
1. Upload PDF with warehouse SOPs
2. Question: "What is the return procedure for damaged goods?"
Response: Answer extracted from document + source chunks
```

### Vision Analysis
```
1. Upload warehouse photo
2. Question: "How many boxes are visible?"
Response: OCR text + box count + damage analysis
```

## 📈 Performance Metrics

Access real-time metrics at `/api/v1/metrics`:
- Total requests and error rate
- Average response time
- Cache hit rate (target: 60%+)
- Token usage and cost tracking
- Redis status

## 🔒 Security

- Google OAuth authentication
- Rate limiting (10 requests/minute)
- Read-only SQL queries
- Input validation and sanitization
- Environment variable management

## 🚀 Deployment to kubeletto.com

### Prerequisites
- Docker image built and pushed to registry
- kubeletto.com account
- Environment variables configured

### Deployment Steps
1. Build Docker images
2. Push to container registry
3. Configure environment variables in kubeletto.com
4. Deploy backend service
5. Deploy frontend service
6. Configure Redis connection
7. Set up SSL certificates
8. Configure health checks

### Environment Variables for Production
- Update `NEXTAUTH_URL` to production domain
- Use production Google OAuth redirect URIs
- Use production Redis Cloud endpoint
- Configure proper secrets management

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test
```

## 📝 License

Proprietary - All rights reserved

## 👨‍💻 Tech Stack

- **Backend**: Python, FastAPI, LangGraph, SQLAlchemy, Redis
- **AI**: Groq LLM, LangChain, FAISS, Tesseract
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Database**: PostgreSQL (Neon)
- **Infrastructure**: Docker, kubeletto.com

## 🎨 Design

- **Font**: Inter
- **Colors**: Slate/Indigo theme
- **Style**: Enterprise SaaS, clean and professional
- **Inspiration**: ChatGPT/Claude interface

## 📧 Contact

For support: admin@invensight.ai

---

**Built with ❤️ for AI-powered warehouse analytics**
