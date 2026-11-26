from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3, os, uuid
from urllib.parse import parse_qs, urlparse
from email.parser import BytesParser
from email.policy import default

IBAN_NO = "TR43 0004 6001 4788 8000 3997 07"
ALICI_AD = "Semih Eymen Uçar"
BANKA_ADI = "Akbank"
GIZLI = "otoyol_gizli_9988"

db = sqlite3.connect("otoyol.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS musteriler (anahtar TEXT PRIMARY KEY, ad TEXT, kalan_hak INTEGER, toplam_gecis INTEGER, dosya_adi TEXT)")
db.execute("INSERT OR IGNORE INTO musteriler VALUES ('anahtar_oyun_studyo_1', 'Indie Oyun Ekibi', 10, 0, 'oyun_yama_v1.pak')")
db.commit()

os.makedirs("dosyalar", exist_ok=True)
with open("dosyalar/oyun_yama_v1.pak", "wb") as f:
    f.write(b"GERCEK_OYUN_VERI_PAKETI_1001" * 100)

class Otoyol(BaseHTTPRequestHandler):
    def html(self, kod, metin):
        self.send_response(kod)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(metin.encode("utf-8"))

    def gonder(self, key, indir):
        row = db.execute("SELECT kalan_hak, dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
        if not row:
            self.html(401, "<body style='background:#0f172a;color:white;padding:30px;'><h3>Geçersiz Anahtar</h3><a href='/' style='color:#38bdf8;'>Geri</a></body>")
            return
        kalan, d_adi = row
        if indir:
            if kalan <= 0:
                self.html(402, "<body style='background:#0f172a;color:white;padding:30px;'><h3>Kotanız Bitti</h3><a href='/' style='color:#38bdf8;'>Geri</a></body>")
                return
            db.execute("UPDATE musteriler SET kalan_hak=kalan_hak-1, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (key,))
            db.commit()

        yol = os.path.join("dosyalar", d_adi or "oyun_yama_v1.pak")
        if not os.path.exists(yol):
            yol = "dosyalar/oyun_yama_v1.pak"
        ad = os.path.basename(yol).replace(key + "_", "")
        veri = open(yol, "rb").read()

        if indir:
            tur, disp = "application/octet-stream", f'attachment; filename="{ad}"'
        else:
            k = ad.lower()
            tur = "image/jpeg" if k.endswith((".jpg", ".jpeg")) else "image/png" if k.endswith(".png") else "application/pdf" if k.endswith(".pdf") else "text/plain; charset=utf-8"
            disp = "inline"

        self.send_response(200)
        self.send_header("Content-Type", tur)
        self.send_header("Content-Length", str(len(veri)))
        self.send_header("Content-Disposition", disp)
        self.end_headers()
        self.wfile.write(veri)

    def do_GET(self):
        p = urlparse(self.path)
        q = parse_qs(p.query)
        key = "".join(q.get("anahtar", [])).strip()

        if p.path == "/yonetim":
            if "".join(q.get("sifre", [])) != GIZLI:
                self.html(403, "Yetkisiz"); return
            if "ekle" in q:
                db.execute("UPDATE musteriler SET kalan_hak=kalan_hak+1000 WHERE anahtar=?", ("".join(q.get("ekle", [])),))
                db.commit()
            rows = db.execute("SELECT anahtar, ad, kalan_hak, toplam_gecis, dosya_adi FROM musteriler").fetchall()
            tr = ""
            for k, ad, kalan, gecis, dosya in rows:
                temiz = (dosya or "oyun_yama_v1.pak").replace(k + "_", "")
                tr += f"<tr><td>{ad}</td><td><code>{k}</code></td><td>{kalan}</td><td>{gecis}</td><td>{temiz}</td><td><a href='/onizle?anahtar={k}' target='_blank' style='color:#38bdf8;margin-right:10px;'>👁️ Gör</a><a href='/yonetim?sifre={GIZLI}&ekle={k}' style='color:#10b981;'>+1000 Hak</a></td></tr>"
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:24px;'><h2>🎛️ Veri Otoyolu Kokpit</h2><table border='1' cellpadding='10' style='border-collapse:collapse;width:100%;border-color:#334155;'><tr><th>Proje</th><th>Anahtar</th><th>Kalan</th><th>Geçiş</th><th>Dosya</th><th>İşlem</th></tr>{tr}</table><br><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>")
            return

        if p.path == "/otomatik-onay":
            if "".join(q.get("gizli", [])) != GIZLI:
                self.send_response(403); self.end_headers(); return
            db.execute("UPDATE musteriler SET kalan_hak=kalan_hak+1000 WHERE anahtar=?", (key,))
            db.commit(); self.send_response(200); self.end_headers(); self.wfile.write(b"OK"); return

        if p.path == "/indir":
            self.gonder(key, True); return

        if p.path == "/onizle":
            self.gonder(key, False); return

        if p.path == "/kontrol":
            r = db.execute("SELECT ad, kalan_hak, dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
            if not r:
                self.html(200, "<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>❌ Anahtar Bulunamadı</h3><a href='/' style='color:#38bdf8;'>← Geri</a></body>")
                return
            ad_p, kalan_p, dosya_p = r
            temiz = (dosya_p or "oyun_yama_v1.pak").replace(key + "_", "")
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>📂 Depo Durumu</h2><p><b>Proje:</b> {ad_p}</p><p><b>Dosya:</b> {temiz}</p><p><b>Kalan Hak:</b> {kalan_p}</p><a href='/indir?anahtar={key}' style='display:inline-block;background:#10b981;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;'>⬇️ İndir</a> <a href='/onizle?anahtar={key}' target='_blank' style='display:inline-block;background:#3b82f6;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;margin-left:8px;'>👁️ İndirmeden Gör</a><br><br><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>")
            return

        if p.path == "/" and not self.headers.get("X-API-Key"):
            self.html(200, f"<!DOCTYPE html><html lang='tr'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Veri Otoyolu</title><style>body{{font-family:sans-serif;background:#0f172a;color:#f8fafc;max-width:680px;margin:20px auto;padding:16px}}.kutu{{background:#1e293b;padding:20px;border-radius:12px;margin-bottom:16px;border:1px solid #334155}}input,button{{padding:12px;border-radius:8px;border:none;font-size:15px;margin-top:8px;width:100%;box-sizing:border-box}}input{{background:#0f172a;color:white;border:1px solid #475569}}button{{background:#3b82f6;color:white;font-weight:bold}}.yesil{{background:#10b981}}.mor{{background:#8b5cf6}}</style></head><body><h1>🚀 Veri Otoyolu</h1><div class='kutu'><h3>1. Ücretsiz Anahtar Al</h3><form method='POST' action='/kayit'><input name='ad' placeholder='Proje Adı' required><button>API Anahtarı Üret</button></form></div><div class='kutu'><h3>2. Dosya Yükle</h3><form method='POST' action='/yukle' enctype='multipart/form-data'><input name='anahtar' placeholder='vo_...' required><input type='file' name='dosya' required><button class='yesil'>Yükle</button></form></div><div class='kutu'><h3>3. Dosyamı Gör ve İndir</h3><form method='GET' action='/kontrol'><input name='anahtar' placeholder='vo_...' required><button class='mor'>📂 Dosyamı Görüntüle</button></form></div><div class='kutu'><h3>4. Otomatik Kota (100 TL = 1000 Hak)</h3><p><b>{BANKA_ADI} - {ALICI_AD}</b><br>IBAN: <code>{IBAN_NO}</code><br><small>Açıklamaya sadece API anahtarınızı yazın.</small></p></div></body></html>")
            return
        self.gonder(self.headers.get("X-API-Key"), True)

    def do_POST(self):
        ham = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/kayit":
            ad = "".join(parse_qs(ham.decode()).get("ad", ["Proje"]))
            k = "vo_" + uuid.uuid4().hex[:16]
            db.execute("INSERT INTO musteriler VALUES (?, ?, 10, 0, 'oyun_yama_v1.pak')", (k, ad))
            db.commit()
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>✅ Anahtarınız: <code>{k}</code></h2><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>")
        elif self.path == "/yukle":
            m = BytesParser(policy=default).parsebytes(f"Content-Type: {self.headers.get('Content-Type')}\r\n\r\n".encode() + ham)
            anahtar, d_adi, icerik = "", "", b""
            for part in m.iter_parts():
                if part.get_param("name", header="content-disposition") == "anahtar": anahtar = part.get_content().strip()
                elif part.get_param("name", header="content-disposition") == "dosya": d_adi = part.get_filename() or ""; icerik = part.get_payload(decode=True)
            if not db.execute("SELECT 1 FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone() or not d_adi:
                self.html(400, "<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>❌ Geçersiz Anahtar veya Dosya</h3><a href='/' style='color:#38bdf8;'>Geri</a></body>"); return
            g_ad = f"{anahtar}_{os.path.basename(d_adi)}"
            open(os.path.join("dosyalar", g_ad), "wb").write(icerik)
            db.execute("UPDATE musteriler SET dosya_adi=? WHERE anahtar=?", (g_ad, anahtar))
            db.commit()
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>🚀 Dosya Yüklendi!</h2><a href='/kontrol?anahtar={anahtar}' style='color:#34d399;font-weight:bold;'>📂 Dosyayı Gör ve İndir →</a></body>")

HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), Otoyol).serve_forever()
