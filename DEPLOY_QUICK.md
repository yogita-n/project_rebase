# Quick Deployment Guide

## 🚀 Deploy to Render (Easiest)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Deploy on Render:**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Select "Docker" as runtime
   - Click "Create Web Service"
   - Done! Your app will be live in ~5 minutes

3. **Your URL:** `https://your-service-name.onrender.com`

---

## 🤗 Deploy to Hugging Face Spaces

1. **Create Space:**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Choose "Docker" SDK

2. **Clone and Push:**
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
   cd SPACE_NAME
   
   # Copy files from this project
   cp ../project_rebase/Dockerfile .
   cp ../project_rebase/requirements-prod.txt ./requirements.txt
   cp -r ../project_rebase/core .
   cp -r ../project_rebase/static .
   cp ../project_rebase/app.py .
   cp ../project_rebase/web_server.py .
   cp ../project_rebase/README_HF.md ./README.md
   
   git add .
   git commit -m "Deploy app"
   git push
   ```

3. **Your URL:** `https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME`

---

## 📋 Files Needed for Deployment

✅ Already created:
- `Dockerfile` - Container configuration
- `requirements-prod.txt` - Production dependencies
- `.gitignore` - Files to exclude
- `README_HF.md` - Hugging Face description

---

## 🧪 Test Locally First

```bash
# Build Docker image
docker build -t dep-analyzer .

# Run container
docker run -p 5000:5000 dep-analyzer

# Test at http://localhost:5000
```

---

## 💡 Tips

- **Free Tier**: Both platforms offer free hosting!
- **Build Time**: ~5-10 minutes on first deploy
- **Auto-deploy**: Push to GitHub → Render auto-deploys
- **Custom Domain**: Available on both platforms (paid)

---

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.
