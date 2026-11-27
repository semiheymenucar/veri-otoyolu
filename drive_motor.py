import os, json, requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def _creds_al():
    tok = os.environ.get("DRIVE_TOKEN", "").strip()
    if not tok and os.path.exists("token.json"):
        tok = open("token.json", "r", encoding="utf-8").read().strip()
    if not tok:
        return None
    creds = Credentials.from_authorized_user_info(json.loads(tok), ["https://googleapis.com"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def drive_servis():
    c = _creds_al()
    return build("drive", "v3", credentials=c, cache_discovery=False) if c else None

def havuz_bos_alan():
    srv = drive_servis()
    if not srv:
        return 200 * 1024**3
    try:
        q = srv.about().get(fields="storageQuota").execute().get("storageQuota", {})
        lim, use = int(q.get("limit", 0)), int(q.get("usage", 0))
        if lim > 0:
            return max(0, lim - use)
    except Exception:
        pass
    return 200 * 1024**3

def oturum_ac(uzak_ad, boyut, origin):
    c = _creds_al()
    if not c:
        return None
    h = {"Authorization": f"Bearer {c.token}", "Content-Type": "application/json; charset=UTF-8", "X-Upload-Content-Length": str(boyut), "X-Upload-Content-Type": "application/octet-stream"}
    if origin:
        h["Origin"] = origin
    r = requests.post("https://googleapis.com", headers=h, json={"name": uzak_ad}, timeout=20)
    return r.headers.get("Location") if r.status_code in (200, 201) else None

def dosya_dogrula(file_id):
    srv = drive_servis()
    if not srv:
        return None
    m = srv.files().get(fileId=file_id, fields="id,size,trashed").execute()
    return None if m.get("trashed") else int(m.get("size", 0))

def dosya_sil(file_id):
    srv = drive_servis()
    if srv:
        try: srv.files().delete(fileId=file_id).execute()
        except Exception: pass

def drive_indir_akisi(file_id, wfile):
    srv = drive_servis()
    if not srv:
        return False
    dl = MediaIoBaseDownload(wfile, srv.files().get_media(fileId=file_id), chunksize=8*1024*1024)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return True
