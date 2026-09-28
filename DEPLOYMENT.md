# Deployment Guide - InvenSight AI

## 📦 Push ke GitHub

### **1. Buat Repository di GitHub**
1. Login ke GitHub
2. Klik "New repository"
3. Repository name: `invensight-ai` (atau nama lain)
4. Set sebagai Public (untuk portofolio)
5. Jangan check "Initialize with README" (karena sudah ada)
6. Klik "Create repository"

### **2. Push ke GitHub**

```bash
cd "D:\AI Engineer Projects\InvenSight"

# Tambahkan remote repository
git remote add origin https://github.com/YOUR_USERNAME/invensight-ai.git

# Push ke GitHub
git branch -M main
git push -u origin main
```

**Ganti `YOUR_USERNAME` dengan username GitHub Anda.**

### **3. Repository di GitHub akan berisi:**
- ✅ README.md (dokumentasi)
- ✅ PORTFOLIO.md (dokumentasi portofolio)
- ✅ backend/ (FastAPI code)
- ✅ frontend/ (Next.js code)
- ✅ docker-compose.yml (Docker setup)
- ✅ .gitignore (file yang di-ignore)
- ✅ Dockerfiles (backend & frontend)

---

## 🚀 Deployment ke kubeletto.com

### **Prerequisites**
- GitHub repository sudah dibuat
- Docker images sudah terpush ke container registry (Docker Hub / GHCR)
- Environment variables siap

### **Langkah 1: Push Docker Images ke Container Registry**

**Option A: Docker Hub**
```bash
# Login ke Docker Hub
docker login

# Build backend image
cd backend
docker build -t YOUR_USERNAME/invensight-backend:latest .

# Push ke Docker Hub
docker push YOUR_USERNAME/invensight-backend:latest

# Build frontend image
cd ../frontend
docker build -t YOUR_USERNAME/invensight-frontend:latest .

# Push ke Docker Hub
docker push YOUR_USERNAME/invensight-frontend:latest
```

**Option B: GitHub Container Registry (GHCR)**
```bash
# Login ke GHCR
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Build backend image
cd backend
docker build -t ghcr.io/YOUR_USERNAME/invensight-backend:latest .

# Push ke GHCR
docker push ghcr.io/YOUR_USERNAME/invensight-backend:latest

# Build frontend image
cd ../frontend
docker build -t ghcr.io/YOUR_USERNAME/invensight-frontend:latest .

# Push ke GHCR
docker push ghcr.io/YOUR_USERNAME/invensight-frontend:latest
```

**Ganti `YOUR_USERNAME` dengan username Anda.**

### **Langkah 2: Update docker-compose.yml untuk Production**

Update `docker-compose.yml` untuk menggunakan registry images:

```yaml
version: '3.8'

services:
  backend:
    image: YOUR_USERNAME/invensight-backend:latest  # Ganti dengan registry image
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GROQ_MODEL=${GROQ_MODEL}
      - REDIS_URL=${REDIS_URL}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - NEXTAUTH_URL=${NEXTAUTH_URL}
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
    restart: unless-stopped

  frontend:
    image: YOUR_USERNAME/invensight-frontend:latest  # Ganti dengan registry image
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://YOUR_DOMAIN.com  # Ganti dengan domain production
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - NEXTAUTH_URL=${NEXTAUTH_URL}
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
    depends_on:
      - backend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

### **Langkah 3: Setup Environment Variables di kubeletto.com**

**Environment Variables yang Diperlukan (Copy values dari local .env):**

```env
# Database (Neon PostgreSQL - copy dari backend/.env)
DATABASE_URL=postgresql://user:password@host:port/database

# Groq API (copy dari backend/.env)
GROQ_API_KEY=gsk_YOUR_API_KEY
GROQ_MODEL=openai/gpt-oss-120b

# Redis Cloud (URL dari Redis Cloud console)
REDIS_URL=redis://default:YOUR_PASSWORD@YOUR_HOST:PORT

# Google OAuth (copy dari backend/.env dan frontend/.env.local)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# NextAuth (GANTI dua ini untuk production)
NEXTAUTH_URL=https://your-domain.com  # Ganti dengan domain production kubeletto
NEXTAUTH_SECRET=GENERATE_NEW_SECRET  # Generate dengan: openssl rand -base64 32

# Optional (untuk production - bisa kosongkan jika tidak digunakan)
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Cara Setup di kubeletto.com:**
1. Login ke dashboard kubeletto.com
2. Masuk ke project
3. Cari "Environment Variables" atau "Secrets"
4. Tambahkan semua variables di atas
5. Simpan

### **Langkah 4: Deploy ke kubeletto.com**

**Jika kubeletto mendukung Docker Compose:**
1. Upload `docker-compose.yml` ke kubeletto
2. Configure environment variables
3. Deploy service

**Jika kubeletto adalah Kubernetes-based:**
1. Convert docker-compose ke Kubernetes manifests:
   ```bash
   kompose convert
   ```
2. Upload YAML files ke kubeletto
3. Apply with `kubectl apply -f deployment.yaml`

**Jika kubeletto adalah PaaS (Platform as a Service):**
1. Deploy backend sebagai service:
   - Image: `YOUR_USERNAME/invensight-backend:latest`
   - Port: 8000
   - Environment variables: dari Langkah 3

2. Deploy frontend sebagai service:
   - Image: `YOUR_USERNAME/invensight-frontend:latest`
   - Port: 3000
   - Environment variables: dari Langkah 3

3. Configure domain (e.g., `invensight.kubeletto.com`)

### **Langkah 5: Update Google OAuth Redirect URIs**

**Production:**
1. Buka Google Cloud Console
2. Masuk ke credentials
3. Edit OAuth client ID
4. Tambahkan authorized redirect URI:
   - `https://your-domain.com/api/auth/callback/google`
5. Simpan

**Local:**
- `http://localhost:3000/api/auth/callback/google`
- `http://localhost:3001/api/auth/callback/google`
- dll.

### **Langkah 6: Configure Domain & SSL**

**Di kubeletto.com:**
1. Purchase atau connect domain (opsional)
2. Configure DNS records
3. Enable SSL (HTTPS) - biasanya otomatis di PaaS
4. Update `NEXTAUTH_URL` dengan domain production

---

## 🔍 Verifikasi Deployment

### **Health Check**
```bash
# Backend health
curl https://your-domain.com/health

# Expected: {"status":"ok"}

# Metrics
curl https://your-domain.com/api/v1/metrics
```

### **Check Logs**
- Di kubeletto dashboard, lihat logs untuk backend dan frontend
- Pastikan tidak ada error saat startup

### **Test Endpoints**
1. Test SQL analysis di frontend
2. Test RAG query
3. Test image upload (Vision mode)
4. Test Google OAuth login

---

## 🐛 Troubleshooting

### **1. CORS Error di Production**
**Problem:** Frontend tidak bisa connect ke backend
**Solution:**
```python
# Update backend/main.py CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Production domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **2. Database Connection Error**
**Problem:** Cannot connect to PostgreSQL
**Solution:**
- Verify `DATABASE_URL` is correct
- Check if database is accessible from kubeletto network
- Check SSL mode (Neon requires SSL)

### **3. Redis Connection Error**
**Problem:** Cannot connect to Redis
**Solution:**
- Verify `REDIS_URL` is correct
- Check if Redis Cloud allows connections from kubeletto IP
- Fallback: Disable Redis (set `REDIS_URL=""` in env)

### **4. Google OAuth Error**
**Problem:** OAuth redirect error
**Solution:**
- Verify redirect URI di Google Console
- Verify `NEXTAUTH_URL` is correct
- Check browser console for specific error

### **5. Model Not Found Error**
**Problem:** Groq model deprecated
**Solution:**
- Update `GROQ_MODEL` in environment variables
- Check Groq documentation for available models

---

## 📊 Post-Deployment Checklist

- [ ] Backend health check passes
- [ ] Frontend loads correctly
- [ ] Google OAuth login works
- [ ] SQL analysis works
- [ ] RAG query works
- [ ] Vision upload works
- [ ] Metrics endpoint accessible
- [ ] SSL/HTTPS enabled
- [ ] Domain configured
- [ ] Environment variables correct
- [ ] Logs show no errors
- [ ] Rate limiting working
- [ ] Caching enabled (if Redis configured)

---

## 🎯 Deployment Alternatives

### **Jika kubeletto tidak mendukung Docker:**

**Option A: Vercel (Frontend) + Render (Backend)**
1. Deploy frontend ke Vercel:
   ```bash
   cd frontend
   vercel
   ```
2. Deploy backend ke Render:
   - Connect GitHub repository
   - Select `backend` folder
   - Configure environment variables
   - Deploy

**Option B: Railway**
1. Connect GitHub repository
2. Select service type (Docker)
3. Configure environment variables
4. Deploy

**Option C: Heroku**
1. Create Heroku app
2. Set buildpacks (Python + Node.js)
3. Configure environment variables
4. Deploy from GitHub

---

## 💡 Tips untuk Production

1. **Monitor Resource Usage:**
   - CPU, Memory, Disk usage
   - API rate limiting logs
   - Error rate tracking

2. **Backup Database:**
   - Neon memiliki automatic backup
   - Export data secara regular

3. **Update Dependencies:**
   - Update dependencies secara regular
   - Test thoroughly di staging

4. **Security:**
   - Rotate API keys secara regular
   - Use environment variables untuk secrets
   - Enable rate limiting
   - Monitor suspicious activity

5. **Performance:**
   - Enable Redis caching
   - Monitor response times
   - Optimize slow queries

---

## 📞 Support

- **kubeletto.com Documentation**: Cek dokumentasi resmi untuk deployment spesifik
- **GitHub Issues**: Report bugs di repository
- **Email**: Email support kubeletto jika ada masalah deployment

---

**Selamat Deploy! 🚀**
