from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3, json, os, uuid, cgi
from urllib.parse import parse_qs

db = sqlite3.connect("otoyol.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS musteriler (anahtar TEXT PRIMARY KEY, ad TEXT, kalan_hak INTEGER, toplam_gecis INTEGER, dosya_adi TEXT)")
db.execute("INSERT OR IGNORE INTO musteriler VALUES ('anahtar_oyun_studyo_1', 'Indie Oyun Ekibi', 5, 0, 'oyun_yama_v1.pak')")
db.commit()

os.makedirs("dosyalar", exist_ok=True)
with open("dosyalar/oyun_yama_v1.pak", "wb") as f:
    f.write(b"GERCEK_OYUN_VERI_PAKETI_ICERIGI_10010101" * 250)

SITE_URL = "https://veri-otoyolu.onrender.com"

HTML_SAYFA = f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Veri Otoyolu | Otonom Dağıtım Altyapısı</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #0f172a; color: #f8fafc; max-width: 760px; margin: 40px auto; padding: 20px; }}
  .kutu {{ background: #1e293b; padding: 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; }}
  input, button {{ padding: 12px; border-radius: 8px; border: none; font-size: 15px; margin-top: 8px; }}
  input[type="text"], input[type="file"] {{ width: 95%; background: #0f172a; color: white; border: 1px solid #475569; }}
  button {{ background: #3b82f6; color: white; font-weight: bold; cursor: pointer; width: 100%; }}
  button:hover {{ background: #2563eb; }}
  .btn-yesil {{ background: #10b981; }}
  .btn-yesil:hover {{ background: #059669; }}
  code {{ background: #0f172a; padding: 6px 10px; border-radius: 6px; color: #38bdf8; display: block; margin-top: 8px; overflow-x: auto; }}
</style></head>
<body>
  <h1>🚀 Veri Otoyolu Altyapısı</h1>
  <p>Oyun yamalarınızı ve uygulama verilerinizi yüksek hızla dağıtın. Geçiş başına otomatik ölçümleme.</p>
  
  <div class="kutu">
    <h3>1. Anında Ücretsiz API Anahtarı (Geçiş Kartı) Al</h3>
    <form method="POST" action="/kayit">
      <input type="text" name="ad" placeholder="Stüdyo veya Uygulama Adınız" required>
      <button type="submit">Anahtar Üret (10 Ücretsiz Geçiş Hakkı)</button>
    </form>
  </div>

  <div class="kutu">
    <h3>2. Dağıtılacak Dosyanızı Sisteme Yükleyin</h3>
    <form method="POST" action="/yukle" enctype="multipart/form-data">
      <input type="text" name="anahtar" placeholder="API Anahtarınız (vo_...)" required>
      <input type="file" name="dosya" required>
      <button type="submit" class="btn-yesil">Dosyayı Otoyola Yükle</button>
    </form>
  </div>

  <div class="kutu">
    <h3>3. Yazılımınıza veya Oyununuzun Güncelleyicisine Bağlayın</h3>
    <p>Kullanıcılarınıza dosyayı ulaştırmak için tek satır istek yeterlidir:</p>
    <code>curl -H "X-API-Key: ANAHTARINIZ" {SITE_URL} -o guncelleme.pak</code>
  </div>
</body></html>"""

class VeriOtoyoluBulut(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" and not self.headers.get("X-API-Key"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_SAYFA.encode())
            return

        api_key = self.headers.get("X-API-Key")
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
            self.wfile.write(json.dumps({"hata": "Kotaniz bitti! Yeni paket satin alin."}).encode())
            return

        db.execute("UPDATE musteriler SET kalan_hak = kalan_hak - 1, toplam_gecis = toplam_gecis + 1 WHERE anahtar=?", (api_key,))
        db.commit()

        dosya_yolu = os.path.join("dosyalar", dosya_adi or "oyun_yama_v1.pak")
        if not os.path.exists(dosya_yolu):
            dosya_yolu = "dosyalar/oyun_yama_v1.pak"

        with open(dosya_yolu, "rb") as f:
            veri = f.read()

        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(dosya_yolu)}"')
        self.send_header("X-Kalan-Hak", str(kalan_hak - 1))
        self.end_headers()
        self.wfile.write(veri)

    def do_POST(self):
        if self.path == "/kayit":
            uzunluk = int(self.headers.get("Content-Length", 0))
            veriler = parse_qs(self.rfile.read(uzunluk).decode())
            ad = veriler.get("ad", ["Isimsiz Proje"])[0]
            yeni_anahtar = "vo_" + uuid.uuid4().hex[:16]
            db.execute("INSERT INTO musteriler VALUES (?, ?, 10, 0, 'oyun_yama_v1.pak')", (yeni_anahtar, ad))
            db.commit()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            cevap = f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:40px;'><h2>✅ Kayıt Başarılı: {ad}</h2><p>Özel API Anahtarınız: <code style='color:#38bdf8;font-size:18px;'>{yeni_anahtar}</code></p><p>Tanımlanan Ücretsiz Geçiş Hakkı: <b>10</b></p><a href='/' style='color:#93c5fd;'>← Ana Sayfaya Dön ve Dosya Yükle</a></body>"
            self.wfile.write(cevap.encode())

        elif self.path == "/yukle":
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            anahtar = form.getvalue("anahtar", "").strip()
            dosya_alani = form["dosya"] if "dosya" in form else None

            row = db.execute("SELECT ad FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone()
            if not row or not dosya_alani or not dosya_alani.filename:
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("<body style='background:#0f172a;color:white;padding:40px;'><h3>❌ Hata: Geçersiz API Anahtarı veya dosya seçilmedi.</h3><a href='/' style='color:#93c5fd;'>Geri Dön</a></body>".encode())
                return

            guvenli_ad = f"{anahtar}_{os.path.basename(dosya_alani.filename)}"
            with open(os.path.join("dosyalar", guvenli_ad), "wb") as f:
                f.write(dosya_alani.file.read())

            db.execute("UPDATE musteriler SET dosya_adi=? WHERE anahtar=?", (guvenli_ad, anahtar))
            db.commit()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            cevap = f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:40px;'><h2>🚀 Dosya Otoyola Yüklendi!</h2><p><b>{dosya_alani.filename}</b> artık senin API anahtarınla tüm dünyaya dağıtıma hazır.</p><p>Test komutu: <code style='color:#38bdf8;'>curl -H \"X-API-Key: {anahtar}\" {SITE_URL} -o {dosya_alani.filename}</code></p><a href='/' style='color:#93c5fd;'>← Ana Sayfaya Dön</a></body>"
            self.wfile.write(cevap.encode())

port = int(os.environ.get("PORT", 8080))
print(f"Veri Otoyolu V2 Bulut Motoru {port} portunda yayinda...")
HTTPServer(("0.0.0.0", port), VeriOtoyoluBulut).serve_forever()
