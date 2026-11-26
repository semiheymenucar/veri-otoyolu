from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3, json, os, uuid
from urllib.parse import parse_qs, urlparse
from email.parser import BytesParser
from email.policy import default

IBAN_NO = "TR43 0004 6001 4788 8000 3997 07"
ALICI_AD = "Semih Eymen Uçar"
BANKA_ADI = "Akbank"
GIZLI_ANAHTAR = "otoyol_gizli_9988"

db = sqlite3.connect("otoyol.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS musteriler (anahtar TEXT PRIMARY KEY, ad TEXT, kalan_hak INTEGER, toplam_gecis INTEGER, dosya_adi TEXT)")
db.execute("INSERT OR IGNORE INTO musteriler VALUES ('anahtar_oyun_studyo_1', 'Indie Oyun Ekibi', 10, 0, 'oyun_yama_v1.pak')")
db.commit()

os.makedirs("dosyalar", exist_ok=True)
with open("dosyalar/oyun_yama_v1.pak", "wb") as f:
    f.write(b"GERCEK_OYUN_VERI_PAKETI_ICERIGI_10010101" * 250)

SITE_URL = "https://onrender.com"

class VeriOtoyoluBulut(BaseHTTPRequestHandler):
    def dosya_teslim_et(self, api_key):
        row = db.execute("SELECT ad, kalan_hak, toplam_gecis, dosya_adi FROM musteriler WHERE anahtar=?", (api_key,)).fetchone()
        if not row:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(json.dumps({"hata": "Gecersiz API Anahtari!"}).encode())
            return
        ad, kalan_hak, toplam_gecis, dosya_adi = row
        if kalan_hak <= 0:
            self.send_response(402)
            self.end_headers()
            self.wfile.write(json.dumps({"hata": "Kotaniz bitti!"}).encode())
            return
        db.execute("UPDATE musteriler SET kalan_hak = kalan_hak - 1, toplam_gecis = toplam_gecis + 1 WHERE anahtar=?", (api_key,))
        db.commit()
        dosya_yolu = os.path.join("dosyalar", dosya_adi or "oyun_yama_v1.pak")
        if not os.path.exists(dosya_yolu):
            dosya_yolu = "dosyalar/oyun_yama_v1.pak"
        with open(dosya_yolu, "rb") as f:
            veri = f.read()
        orijinal_ad = os.path.basename(dosya_yolu).replace(f"{api_key}_", "")
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f'attachment; filename="{orijinal_ad}"')
        self.send_header("X-Kalan-Hak", str(kalan_hak - 1))
        self.end_headers()
        self.wfile.write(veri)
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == "/otomatik-onay":
            if params.get("gizli", [""]) != GIZLI_ANAHTAR:
                self.send_response(403); self.end_headers(); return
            k = params.get("anahtar", [""]).strip()
            db.execute("UPDATE musteriler SET kalan_hak = kalan_hak + 1000 WHERE anahtar=?", (k,))
            db.commit(); self.send_response(200); self.end_headers(); self.wfile.write(b"OK"); return
        if parsed.path == "/indir":
            self.dosya_teslim_et(params.get("anahtar", [""]).strip()); return
        if parsed.path == "/kontrol":
            key = params.get("anahtar", [""]).strip()
            row = db.execute("SELECT ad, kalan_hak, toplam_gecis, dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
            if not row:
                self.wfile.write("<body style='background:#0f172a;color:white;padding:40px;'><h3>Gecersiz Anahtar</h3><a href='/'>Geri</a></body>".encode()); return
            ad, kalan, toplam, d_adi = row
            temiz = (d_adi or "oyun_yama_v1.pak").replace(f"{key}_", "")
            self.wfile.write(f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>📂 Depo Durumu</h2><p><b>Proje:</b> {ad}</p><p><b>Dosya:</b> {temiz}</p><p><b>Kalan Hak:</b> {kalan}</p><a href='/indir?anahtar={key}' style='display:inline-block;background:#10b981;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;'>⬇️ Dosyayı İndir</a><br><br><a href='/' style='color:#93c5fd;'>← Geri</a></body>".encode()); return
        if parsed.path == "/" and not self.headers.get("X-API-Key"):
            html = f"<!DOCTYPE html><html lang='tr'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Veri Otoyolu</title><style>body{{font-family:sans-serif;background:#0f172a;color:#f8fafc;max-width:720px;margin:20px auto;padding:16px}}.kutu{{background:#1e293b;padding:20px;border-radius:12px;margin-bottom:16px;border:1px solid #334155}}input,button{{padding:12px;border-radius:8px;border:none;font-size:15px;margin-top:8px;width:100%;box-sizing:border-box}}input{{background:#0f172a;color:white;border:1px solid #475569}}button{{background:#3b82f6;color:white;font-weight:bold;cursor:pointer}}.yesil{{background:#10b981}}.mor{{background:#8b5cf6}}</style></head><body><h1>🚀 Veri Otoyolu</h1><div class='kutu'><h3>1. Ücretsiz Anahtar Al</h3><form method='POST' action='/kayit'><input name='ad' placeholder='Proje Adı' required><button>API Anahtarı Üret</button></form></div><div class='kutu'><h3>2. Dosya Yükle</h3><form method='POST' action='/yukle' enctype='multipart/form-data'><input name='anahtar' placeholder='vo_...' required><input type='file' name='dosya' required><button class='yesil'>Yükle</button></form></div><div class='kutu'><h3>3. Dosyamı Gör ve İndir</h3><form method='GET' action='/kontrol'><input name='anahtar' placeholder='vo_...' required><button class='mor'>📂 Dosyamı Görüntüle</button></form></div><div class='kutu'><h3>4. Otomatik Kota (100 TL = 1000 Hak)</h3><p><b>{BANKA_ADI} - {ALICI_AD}</b><br>IBAN: <code>{IBAN_NO}</code><br><small>Açıklamaya sadece API anahtarınızı yazın.</small></p></div></body></html>"
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers(); self.wfile.write(html.encode()); return
        self.dosya_teslim_et(self.headers.get("X-API-Key"))

    def do_POST(self):
        ham = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/kayit":
            ad = parse_qs(ham.decode()).get("ad", ["Proje"])[0]
            k = "vo_" + uuid.uuid4().hex[:16]
            db.execute("INSERT INTO musteriler VALUES (?, ?, 10, 0, 'oyun_yama_v1.pak')", (k, ad)); db.commit()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
            self.wfile.write(f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>✅ Anahtarınız: {k}</h2><a href='/' style='color:#93c5fd;'>← Geri</a></body>".encode())
        elif self.path == "/yukle":
            mesaj = BytesParser(policy=default).parsebytes(f"Content-Type: {self.headers.get('Content-Type')}\r\n\r\n".encode() + ham)
            anahtar, d_adi, icerik = "", "", b""
            for p in mesaj.iter_parts():
                if p.get_param("name", header="content-disposition") == "anahtar": anahtar = p.get_content().strip()
                elif p.get_param("name", header="content-disposition") == "dosya": d_adi = p.get_filename() or ""; icerik = p.get_payload(decode=True)
            if not db.execute("SELECT 1 FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone() or not d_adi:
                self.send_response(400); self.end_headers(); self.wfile.write(b"Hata"); return
            g_ad = f"{anahtar}_{os.path.basename(d_adi)}"
            open(os.path.join("dosyalar", g_ad), "wb").write(icerik)
            db.execute("UPDATE musteriler SET dosya_adi=? WHERE anahtar=?", (g_ad, anahtar)); db.commit()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
            self.wfile.write(f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>🚀 Yüklendi!</h2><a href='/kontrol?anahtar={anahtar}' style='color:#34d399;font-weight:bold;'>📂 Dosyayı Gör ve İndir →</a></body>".encode())

HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), VeriOtoyoluBulut).serve_forever()
