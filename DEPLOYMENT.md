# Deployment Guide: Render & Hugging Face Spaces

This guide explains how to deploy the Dependency Analysis System to cloud platforms.

---

## 🚀 Option 1: Deploy to Render

Render is perfect for deploying web applications with Docker support.

### Prerequisites
- GitHub account
- Render account (free tier available at https://render.com)

### Step-by-Step Instructions

#### 1. Push Code to GitHub

```bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Initial commit: Dependency Analysis System"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

#### 2. Deploy on Render

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +"** → **"Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service:**
   - **Name**: `dependency-analyzer` (or your choice)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Runtime**: `Docker`
   - **Instance Type**: `Free` (or paid for better performance)

5. **Environment Variables** (Optional):
   - `OPENAI_API_KEY`: Your OpenAI key (for AI fixes)

6. **Click "Create Web Service"**

#### 3. Wait for Deployment

- Render will automatically build the Docker image
- Build time: ~5-10 minutes
- You'll get a URL like: `https://dependency-analyzer.onrender.com`

#### 4. Test Your Deployment

Visit your Render URL and test with a repository!

### Render Configuration Files

✅ **Dockerfile** - Already created
✅ **requirements-prod.txt** - Production dependencies

---

## 🤗 Option 2: Deploy to Hugging Face Spaces

Hugging Face Spaces is great for ML/AI applications with free GPU support.

### Prerequisites
- Hugging Face account (free at https://huggingface.co)

### Step-by-Step Instructions

#### 1. Create a New Space

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Configure:
   - **Space name**: `dependency-analyzer`
   - **License**: `MIT`
   - **Space SDK**: `Docker`
   - **Visibility**: `Public` or `Private`

#### 2. Clone Your Space

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/dependency-analyzer
cd dependency-analyzer
```

#### 3. Copy Files to Space

Copy these files from your project:
```bash
# Core files
cp -r core/ dependency-analyzer/
cp -r static/ dependency-analyzer/
cp app.py dependency-analyzer/
cp web_server.py dependency-analyzer/

# Deployment files
cp Dockerfile dependency-analyzer/
cp requirements-prod.txt dependency-analyzer/requirements.txt

# Create README for Hugging Face
```

#### 4. Create Hugging Face README

Create `README.md` in the space directory:

```markdown
---
title: Dependency Analysis System
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Dependency Analysis System

Analyze Python dependencies and detect breaking changes in real-time!

Enter a GitHub repository URL to get started.
```

#### 5. Push to Hugging Face

```bash
cd dependency-analyzer
git add .
git commit -m "Deploy Dependency Analysis System"
git push
```

#### 6. Wait for Build

- Hugging Face will build your Docker image
- Build time: ~5-10 minutes
- Your space will be live at: `https://huggingface.co/spaces/YOUR_USERNAME/dependency-analyzer`

---

## 🐳 Docker Configuration

The included **Dockerfile** is optimized for both platforms:

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install git for cloning repos
RUN apt-get update && apt-get install -y git

# Install dependencies
COPY requirements-prod.txt .
RUN pip install -r requirements-prod.txt

# Copy application
COPY . .

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "web_server:app"]
```

**Key Features:**
- ✅ Python 3.11 slim image (smaller size)
- ✅ Git installed (for cloning GitHub repos)
- ✅ Gunicorn production server
- ✅ 2 workers for better performance
- ✅ 300s timeout (for long analyses)

---

## 📋 Production Checklist

Before deploying, ensure:

- [ ] All files committed to Git
- [ ] `requirements-prod.txt` has all dependencies
- [ ] Dockerfile builds successfully locally:
  ```bash
  docker build -t dep-analyzer .
  docker run -p 5000:5000 dep-analyzer
  ```
- [ ] Environment variables configured (if using OpenAI)
- [ ] `.gitignore` excludes sensitive files

---

## 🔧 Environment Variables

Set these in your deployment platform:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Optional | For AI-powered migration fixes |
| `FLASK_ENV` | No | Set to `production` |

---

## 🌐 Custom Domain (Render)

1. Go to your service settings
2. Click **"Custom Domain"**
3. Add your domain (e.g., `analyzer.yourdomain.com`)
4. Update DNS records as instructed

---

## 📊 Monitoring & Logs

### Render
- **Logs**: Dashboard → Your Service → Logs tab
- **Metrics**: CPU, Memory, Request count
- **Health Check**: Automatic via `/api/health`

### Hugging Face
- **Logs**: Space page → "Logs" tab
- **Rebuild**: Click "Factory reboot" if needed

---

## 🐛 Troubleshooting

### Build Fails

**Check:**
- All files are committed
- `requirements-prod.txt` is valid
- Dockerfile syntax is correct

**Solution:**
```bash
# Test locally first
docker build -t test-build .
```

### App Crashes on Startup

**Check logs for:**
- Missing dependencies
- Port binding issues
- Import errors

**Common fix:**
```bash
# Add missing package to requirements-prod.txt
pip freeze | grep package-name >> requirements-prod.txt
```

### Timeout Errors

**For long analyses:**
- Increase timeout in Dockerfile: `--timeout 600`
- Use paid tier for better performance

### Out of Memory

**Solutions:**
- Reduce workers: `--workers 1`
- Upgrade to paid tier
- Optimize code to use less memory

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Render** | 750 hrs/month | $7/month+ | Production apps |
| **Hugging Face** | Unlimited | Free GPU | ML/AI demos |

---

## 🚀 Quick Deploy Commands

### Test Locally with Docker
```bash
docker build -t dep-analyzer .
docker run -p 5000:5000 dep-analyzer
# Visit http://localhost:5000
```

### Deploy to Render
```bash
git push origin main
# Render auto-deploys on push
```

### Deploy to Hugging Face
```bash
cd your-hf-space
git add .
git commit -m "Update"
git push
```

---

## 📱 Post-Deployment

After deployment:

1. **Test the live app** with a sample repository
2. **Share the URL** with users
3. **Monitor logs** for errors
4. **Set up alerts** (optional)
5. **Add custom domain** (optional)

---

## 🎯 Next Steps

- [ ] Deploy to Render or Hugging Face
- [ ] Test with real repositories
- [ ] Add custom domain (optional)
- [ ] Enable HTTPS (automatic on both platforms)
- [ ] Set up monitoring/alerts
- [ ] Share with the community!

---

**Need help?** Check the platform documentation:
- Render: https://render.com/docs
- Hugging Face: https://huggingface.co/docs/hub/spaces
