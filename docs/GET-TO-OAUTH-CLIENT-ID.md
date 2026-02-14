# Get to OAuth 2.0 Client ID (Desktop) — Exact Clicks

**Direct link (opens Credentials page):**  
**https://console.cloud.google.com/apis/credentials**

---

## If the link opened in your browser, do this in order:

### 1. Pick or create a project
- At the **top of the page**, click the **project dropdown** (it says the current project name or "Select a project").
- If you see a project you want: click it.
- If you need a new one: click **"NEW PROJECT"** → name it (e.g. "Faceless Shorts") → **Create**. Then select it.

### 2. Open Credentials (you may already be there)
- In the left sidebar: **APIs & Services** → **Credentials**.
- Or you landed here from the direct link.

### 3. Configure consent screen (only if you’re told to)
- If you see **"Create Credentials"** and can click it, skip to step 4.
- If you’re told to configure the consent screen first:
  - Click **"CONFIGURE CONSENT SCREEN"** (or the prompt they show).
  - Choose **External** (unless you use Google Workspace and want only your org) → **Create**.
  - **App name:** e.g. `Faceless Shorts`. **User support email:** your email. **Developer contact:** your email.
  - Click **Save and Continue** through the steps until you’re back at **Credentials**.

### 4. Create the OAuth 2.0 Client ID
- Click **"+ CREATE CREDENTIALS"** (top of the Credentials page).
- Choose **"OAuth client ID"**.
- **Application type:** **Desktop app**.
- **Name:** e.g. `Faceless Shorts Desktop`.
- Click **Create**.

### 5. Download the JSON
- A popup shows your **Client ID** and **Client secret**.
- Click **"DOWNLOAD JSON"**.
- You get a file like `client_secret_xxxxx.json` or `credentials.json`.

### 6. Put it in your project
- Rename or copy that file to:
  ```
  config/client_secrets.json
  ```
- Put it inside your `faceless-shorts-mvp` project in the `config` folder (same folder as `.env`).

### 7. Enable YouTube Data API v3 (if you haven’t)
- Left sidebar: **APIs & Services** → **Library**.
- Search **"YouTube Data API v3"** → click it → **Enable** (if it says "Manage" it’s already on).
- Go back to **Credentials** and finish step 6 if you hadn’t yet.

---

**Then run:**  
`python3 scripts/auth_youtube.py`  
Sign in in the browser when it opens. Done.
