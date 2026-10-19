# Vercel Deployment Guide

This project now includes a Next.js web frontend for deployment on Vercel with a single public URL.

## Architecture

- **Frontend**: Next.js 14 with React and Tailwind CSS (in `web/` directory)
- **Backend**: FastAPI with Groq, FAISS, and PDF processing (in `backend/` directory)
- **Deployment**: Vercel for Next.js, with API routes proxying to FastAPI backend

## Deployment Options

### Option 1: Fullstack on Vercel (Recommended)

Deploy both frontend and backend as a single Vercel application:

1. **Deploy the backend separately** on a platform that supports long-running processes:
   - Render, Railway, or Fly.io (recommended)
   - Get the backend URL (e.g., `https://your-backend.onrender.com`)

2. **Deploy the frontend on Vercel**:
   - Push this repository to GitHub
   - Go to [Vercel](https://vercel.com) and click "New Project"
   - Import your GitHub repository
   - Set the root directory to `web`
   - Add environment variable:
     - `BACKEND_URL`: Your backend URL from step 1
   - Click "Deploy"

3. **Configure backend CORS**:
   - Update `CORS_ALLOWED_ORIGINS` in your backend to include your Vercel domain
   - Example: `https://your-app.vercel.app`

### Option 2: Hybrid Deployment (Backend on Render, Frontend on Vercel)

1. **Deploy backend on Render**:
   - Use the existing `render.yaml` configuration
   - Get the backend URL

2. **Deploy frontend on Vercel**:
   - Follow Option 1, step 2

### Option 3: Backend as Vercel Serverless Functions (Advanced)

Convert the FastAPI backend to Vercel serverless functions. This requires:
- Refactoring the backend to be stateless
- Using Vercel Postgres or other serverless database
- Handling file uploads with Vercel Blob storage

This is more complex but fully serverless. Contact for guidance if needed.

## Local Development

### Start the backend:
```powershell
cd backend
uvicorn main:app --reload --port 8000
```

### Start the Next.js frontend:
```powershell
cd web
npm install
npm run dev
```

Access the app at `http://localhost:3000`

## Environment Variables

### Backend (.env):
```
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-20b
JWT_SECRET_KEY=your-secret-key
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app
BACKEND_URL=http://localhost:8000
MAX_UPLOAD_BYTES=10485760
TAVILY_API_KEY=your-tavily-api-key (optional)
```

### Frontend (Vercel):
```
BACKEND_URL=https://your-backend-url.com
```

## Migration from Streamlit

The new Next.js frontend provides:
- Better performance and SEO
- Server-side rendering
- Modern React components
- Better mobile experience
- Single URL deployment on Vercel

The Streamlit frontend is still available in `frontend/` for reference or local use.

## Features

- JWT authentication
- PDF document upload and indexing
- AI-powered chat with document context
- Agentic RAG system
- Web search integration (optional)
- User-specific data isolation

## Troubleshooting

### CORS Errors
Ensure `CORS_ALLOWED_ORIGINS` in your backend includes your Vercel domain.

### API Connection Issues
Check that `BACKEND_URL` in Vercel environment variables is correct and accessible.

### File Upload Issues
Ensure the backend has proper storage configuration for uploaded files.

## Support

For issues specific to:
- **Vercel deployment**: Check [Vercel docs](https://vercel.com/docs)
- **Backend issues**: See `DEPLOYMENT.md`
- **General issues**: Check the README.md
