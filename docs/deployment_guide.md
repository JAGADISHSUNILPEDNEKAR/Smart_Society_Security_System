# Cloud Deployment Guide
## Smart Society Security System — Zero-Local-Setup Cloud Hosting

This guide explains how to deploy the **Smart Society Security System** to the cloud so you can access it via a permanent public HTTPS URL from any laptop, tablet, or smartphone without running Python locally.

---

## Recommended Deployment Target: Streamlit Community Cloud (100% Free & 2-Minute Setup)

**Streamlit Community Cloud** is the official, free cloud hosting platform provided by Streamlit for GitHub-hosted applications. It automatically provides:
- Free public HTTPS URL (e.g., `https://smart-society-security.streamlit.app`)
- Automatic HTTPS SSL certificates (mandatory for browser webcam access)
- Automatic continuous deployment (every git push to `main` updates the live app)
- Direct integration with your GitHub repository: `JAGADISHSUNILPEDNEKAR/Smart_Society_Security_System`

### Step-by-Step Deployment on Streamlit Cloud:

1. **Open Streamlit Community Cloud**:
   Go to [share.streamlit.io](https://share.streamlit.io/) in your browser.

2. **Sign In with GitHub**:
   Click **"Continue with GitHub"** and authorize Streamlit using your GitHub account (`JAGADISHSUNILPEDNEKAR`).

3. **Deploy a New App**:
   Click the **"Create app"** or **"New app"** button.

4. **Select Repository Details**:
   - **Repository**: `JAGADISHSUNILPEDNEKAR/Smart_Society_Security_System`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (Optional): Choose a custom subdomain, e.g., `smart-society-security.streamlit.app`

5. **Click "Deploy!"**:
   Streamlit Cloud will:
   - Read `packages.txt` and automatically install system libraries (`libgl1`, `libglib2.0-0` for OpenCV).
   - Read `requirements.txt` and install all Python dependencies.
   - Start the Security Operations Center dashboard.

6. **Access & Test from Anywhere**:
   - Open your public URL on any device.
   - Navigate to **`📹 Live Gate Monitor`**.
   - Select **`Browser Camera Snapshot`** (your browser will ask "Allow camera permission?") to verify live facial recognition using your device's camera over HTTPS!

---

## Alternative Option 2: Hugging Face Spaces (Free Cloud AI Hosting)

Hugging Face Spaces provides free cloud CPU infrastructure ideal for computer vision and machine learning applications.

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and create a free account or sign in.
2. Click **"Create new Space"**.
3. Space details:
   - **Space Name**: `smart-society-security`
   - **License**: MIT or Apache 2.0
   - **Space SDK**: Select **Streamlit** (or **Docker**)
   - **Space Hardware**: Free CPU (2 vCPU, 16 GB RAM)
4. Link to GitHub:
   - You can connect your GitHub repository directly or push your git repository to the Hugging Face remote:
     ```bash
     git remote add space https://huggingface.co/spaces/YOUR_USERNAME/smart-society-security
     git push space main
     ```

---

## Alternative Option 3: Render (Free Web Service / Docker)

Render supports containerized deployments directly from GitHub.

1. Sign up at [dashboard.render.com](https://dashboard.render.com/) with GitHub.
2. Click **"New +"** $\rightarrow$ **"Web Service"**.
3. Select your repository: `JAGADISHSUNILPEDNEKAR/Smart_Society_Security_System`.
4. Configuration:
   - **Environment**: `Docker` (Render will automatically detect the `Dockerfile` we created).
   - **Instance Type**: `Free`
   - **Plan**: Free tier (512 MB RAM, 0.1 CPU).
5. Click **"Create Web Service"**.
6. Render will build the Docker container and deploy the app at a custom `https://smart-society-security.onrender.com` URL.

---

## How Camera Access Works in Cloud Deployments

When deployed on a remote cloud server (e.g. AWS, Streamlit Cloud, Render), the cloud server is a headless virtual machine in a data center without a physical USB webcam attached.

Our application was specifically engineered to support cloud access via:
1. **Browser Camera (`st.camera_input`)**: When you access the website on your phone or laptop, your browser uses the WebRTC MediaDevices API to capture real-time webcam snapshots directly from your client machine and sends the frame to the cloud backend for YuNet detection and SFace recognition.
2. **Photo File Upload**: Upload incident photos or test portraits directly to the gate checkpoint.
3. **Automated Fallback Security Stream**: Automatically engages if no physical camera sensor is detected, preventing any server crashes.

