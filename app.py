from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3, json, os, uuid
from urllib.parse import parse_qs

db = sqlite3.connect("otoyol.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS musteriler (anahtar TEXT PRIMARY KEY, ad TEXT, kalan_hak INTEGER, toplam_gecis INTEGER)")
db.execute("INSERT OR IGNORE INTO musteriler VALUES ('anahtar_oyun_studyo_1', 'Indie Oyun Ekibi', 5, 0)")
db.commit()

os.makedirs("dosyalar", exist_ok=True)
with open("dosyalar/oyun_yama_v1.pak", "wb") as f:
    f.write(b"GERCEK_OYUN_VERI_PAKETI_ICERIGI_10010101" * 250)

HTML_SAYFA = """<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Veri Otoyolu | Otonom Dağıtım Altyapısı</title>
<style>
  body { font-family: -apple-system, sans-serif; background: #0f172a; color: #f8fafc; max-width: 720px; margin: 40px auto; padding: 20px; }
  .kutu { background: #1e293b; padding: 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; }
  input, button { padding: 12px; border-radius: 8px; border: none; font-size: 16px; }
  input { width: 65%; background: #0f172a; color: white; border: 1px solid #475569; }
  button { background: #3b82f6; color: white; font-weight: bold; cursor: pointer; }
  button:hover { background: #2563eb; }
  code { background: #0f172a; padding: 4px 8px; border-radius: 6px; color: #38bdf8; }
</style></head>
<body>
  <h1>🚀 Veri Otoyolu Altyapısı</h1>
  <p>Oyun yamalarınızı ve uygulama verilerinizi yüksek hızla dağıtın. Geçiş başına otomatik ölçümleme.</p>
  <div class="kutu">
    <h3>1. Anında Ücretsiz API Anahtarı (Geçiş Kartı) Al</h3>
    <form method="POST" action="/kayit">
      <input type="text" name="ad" placeholder="Stüdyo veya Uygulama Adınız" required>
      <button type="submit">Anahtar Üret (10 Hak Hediye)</button>
    </form>
  </div>
  <div class="kutu">
    <h3>2. Sistem Nasıl Kullanılır?</h3>
    <p>Yazılımınızdan veya oyununuzdan aşağıdaki uç noktaya <code>X-API-Key</code> başlığı ile istek atmanız yeterlidir:</p>
    <p><code>curl -H "X-API-Key: ANAHTARINIZ" BU_SITENIN_LINKI -o paket.pak</code></p>
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
        row = db.execute("SELECT ad, kalan_hak, toplam_gecis FROM musteriler WHERE anahtar=?", (api_key,)).fetchone()

        if not row:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(json.dumps({"hata": "Gecersiz API Anahtari!"}).encode())
            return

        ad, kalan_hak, toplam_gecis = row
        if kalan_hak <= 0:
            self.send_response(402)
            self.end_headers()
            self.wfile.write(json.dumps({"hata": "Kotaniz bitti! Bakiye yukleyin."}).encode())
            return

        db.execute("UPDATE musteriler SET kalan_hak = kalan_hak - 1, toplam_gecis = toplam_gecis + 1 WHERE anahtar=?", (api_key,))
        db.commit()

        with open("dosyalar/oyun_yama_v1.pak", "rb") as f:
            veri = f.read()

        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", 'attachment; filename="oyun_yama_v1.pak"')
        self.send_header("X-Kalan-Hak", str(kalan_hak - 1))
        self.end_headers()
        self.wfile.write(veri)

    def do_POST(self):
        if self.path == "/kayit":
            uzunluk = int(self.headers.get("Content-Length", 0))
            govde = self.rfile.read(uzunluk).decode()
            veriler = parse_qs(govde)
            ad = veriler.get("ad", ["Isimsiz Proje"])[0]
            yeni_anahtar = "vo_" + uuid.uuid4().hex[:16]
            db.execute("INSERT INTO musteriler VALUES (?, ?, 10, 0)", (yeni_anahtar, ad))
            db.commit()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            cevap = f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:40px;'><h2>✅ Kayıt Başarılı: {ad}</h2><p>Özel API Anahtarınız: <code style='color:#38bdf8;font-size:18px;'>{yeni_anahtar}</code></p><p>Tanımlanan Ücretsiz Geçiş Hakkı: <b>10</b></p><a href='/' style='color:#93c5fd;'>← Geri Dön</a></body>"
            self.wfile.write(cevap.encode())

port = int(os.environ.get("PORT", 8080))
print(f"Veri Otoyolu Self-Servis Motoru {port} portunda yayinda...")
HTTPServer(("0.0.0.0", port), VeriOtoyoluBulut).serve_forever()
