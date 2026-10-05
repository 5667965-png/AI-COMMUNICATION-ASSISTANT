# Deploy the AI Communication Assistant on Streamlit — FREE

Streamlit Community Cloud (share.streamlit.io) is free and hosts this app
at a public URL like `https://aca-isl.streamlit.app`.

The ISL model (`backend/model/trained_model/isl_sign_model.pkl`, 17 MB)
is already tracked in Git, so it deploys with the repo automatically.

---

## Step 1 — Push the project to GitHub

The project is already a Git repository. From the project folder:

```bash
# create a NEW empty repository on github.com first, then:
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

> GitHub's file limit is 100 MB — the 17 MB model is fine.

## Step 2 — Deploy on Streamlit Community Cloud

1. Open **https://share.streamlit.io** and sign in with GitHub.
2. Click **New app**.
3. Settings:
   - **Repository:** select your repository
   - **Branch:** `main`
   - **Main file path:** `streamlit_app/streamlit_app.py`
   - **App URL:** pick a name (e.g. `aca-isl`)
4. Click **Deploy**.

Streamlit Cloud reads the root `requirements.txt` and installs
Streamlit, MediaPipe, OpenCV, scikit-learn and gTTS automatically.

## Step 3 — Open the app

After ~2–5 minutes you get a live URL:

```
https://<app-name>.streamlit.app
```

Features available online:
- 🤟 ISL sign detection (camera or photo upload)
- 🧠 AI natural sentence builder
- 🔊 Text-to-speech (English / Hindi / Marathi)
- ⚡ Quick messages, ⭐ favorites, 🕘 history
- 🚨 Emergency message center

## Free-tier notes

- Apps **sleep after ~7 days** of inactivity (wake on visit, ~30 s).
- **1 GB RAM** limit — the ISL model uses only ~50 MB, so it fits.
- No credit card required, ever.

## Run locally first (optional)

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run streamlit_app.py
# opens http://localhost:8501
```
