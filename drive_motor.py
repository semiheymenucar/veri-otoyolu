import os, json, io, requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

def drive_servis():
    tok = os.environ.get("DRIVE_TOKEN", "").strip()
    if not tok and os.path.exists("token.json"):
        tok = open("token.json", "r", encoding="utf-8").read().strip()
    if not tok:
        return None
    info = json.loads(tok)
    creds = Credentials.from_authorized_user_info(info, ["https://googleapis.com"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def drive_yukle(yerel_yol, uzak_ad):
    srv = drive_servis()
    if not srv:
        return None
    meta = {"name": uzak_ad}
    media = MediaFileUpload(yerel_yol, chunksize=5*1024*1024, resumable=True)
    req = srv.files().create(body=meta, media_body=media, fields="id")
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp.get("id")

def drive_indir_akisi(file_id, wfile):
    srv = drive_servis()
    if not srv:
        return False
    req = srv.files().get_media(fileId=file_id)
    dl = MediaIoBaseDownload(wfile, req, chunksize=5*1024*1024)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return True
