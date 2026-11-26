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

SITE_URL = "https://veri-otoyolu.onrender.com"

class VeriOtoyoluBulut(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        # OTOMATİK ONAY SİNYALİ
        if parsed.path == "/otomatik-onay":
            params = parse_qs(parsed.query)
            if params.get("gizli", [""])[0] != GIZLI_ANAHTAR:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Yetkisiz")
                return
            musteri_key = params.get("anahtar", [""])[0].strip()
            db.execute("UPDATE musteriler SET kalan_hak = kalan_hak + 1000 WHERE anahtar=?", (musteri_key,))
            db.commit()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"OK: {musteri_key} +1000 hak yuklendi".encode())
            return

        if parsed.path == "/" and not self.headers.get("X-API-Key"):
            html = f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Veri Otoyolu | Tam Otonom Dağıtım Altyapısı</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #0f172a; color: #f8fafc; max-width: 760px; margin: 40px auto; padding: 20px; }}
  .kutu {{ background: #1e293b; padding: 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; }}
  .iban-kutu {{ background: #0f172a; padding: 16px; border-radius: 8px; border: 1px dashed #10b981; margin: 10px 0; }}
  input, button {{ padding: 12px; border-radius: 8px; border: none; font-size: 15px; margin-top: 8px; display: block; }}
  input[type="text"], input[type="file"] {{ width: 96%; background: #0f172a; color: white; border: 1px solid #475569; }}
  button {{ background: #3b82f6; color: white; font-weight: bold; cursor: pointer; width: 100%; }}
  .btn-yesil {{ background: #10b981; }}
  code {{ background: #0f172a; padding: 8px 12px; border-radius: 6px; color: #38bdf8; display: block; margin-top: 8px; }}
</style></head>
<body>
  <h1>🚀 Veri Otoyolu Altyapısı</h1>
  <p>Oyun yamalarınızı ve uygulama verilerinizi yüksek hızla dağıtın. Tam otonom bakiye ve dağıtım sistemi.</p>
  
  <div class="kutu">
    <h3>1. Ücretsiz Test Anahtarı Al (10 Geçiş)</h3>
    <form method="POST" action="/kayit">
      <input type="text" name="ad" placeholder="Stüdyo veya Uygulama Adınız" required>
      <button type="submit">API Anahtarı Üret</button>
    </form>
  </div>

  <div class="kutu">
    <h3>2. Dağıtılacak Dosyanızı Yükleyin</h3>
    <form method="POST" action="/yukle" enctype="multipart/form-data">
      <input type="text" name="anahtar" placeholder="API Anahtarınız (vo_...)" required>
      <input type="file" name="dosya" required>
      <button type="submit" class="btn-yesil">Dosyayı Otoyola Yükle</button>
    </form>
  </div>

  <div class="kutu">
    <h3>3. 7/24 Otomatik Kota Yükleme (1.000 Geçiş = 100 TL)</h3>
    <div class="iban-kutu">
      <div><b>Banka:</b> {BANKA_ADI}</div>
      <div><b>Alıcı:</b> {ALICI_AD}</div>
      <div><b>IBAN:</b> <span style="color:#34d399;font-family:monospace;font-size:16px;">{IBAN_NO}</span></div>
      <p style="color:#fbbf24;margin-bottom:0;">⚡ <b>Önemli:</b> Havale/FAST açıklama kısmına sadece <b>API Anahtarınızı (vo_...)</b> yazın. Sistem ödemeyi algıladığı an <b>1.000 geçiş hakkı</b> hesabınıza otomatik tanımlanır.</p>
    </div>
  </div>

  <div class="kutu">
    <h3>4. Yazılımınıza Bağlayın</h3>
    <code>curl -H "X-API-Key: ANAHTARINIZ" {SITE_URL} -o guncelleme.pak</code>
  </div>
</body></html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
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
            self.wfile.write(json.dumps({"hata": "Kotaniz bitti! IBAN aciklamasina anahtarinizi yazarak bakiye yukleyin."}).encode())
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
        uzunluk = int(self.headers.get("Content-Length", 0))
        ham_veri = self.rfile.read(uzunluk)

        if self.path == "/kayit":
            veriler = parse_qs(ham_veri.decode())
            ad = veriler.get("ad", ["Isimsiz Proje"])[0]
            yeni_anahtar = "vo_" + uuid.uuid4().hex[:16]
            db.execute("INSERT INTO musteriler VALUES (?, ?, 10, 0, 'oyun_yama_v1.pak')", (yeni_anahtar, ad))
            db.commit()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:40px;'><h2>✅ Kayıt Başarılı: {ad}</h2><p>API Anahtarınız: <code style='color:#38bdf8;font-size:18px;'>{yeni_anahtar}</code></p><p>Ücretsiz Test Hakkı: <b>10</b></p><a href='/' style='color:#93c5fd;'>← Ana Sayfaya Dön</a></body>".encode())

        elif self.path == "/yukle":
            baslik = f"Content-Type: {self.headers.get('Content-Type')}\r\n\r\n".encode()
            mesaj = BytesParser(policy=default).parsebytes(baslik + ham_veri)
            anahtar, dosya_adi, dosya_icerigi = "", "", b""
            for parca in mesaj.iter_parts():
                if parca.get_param("name", header="content-disposition") == "anahtar":
                    anahtar = parca.get_content().strip()
                elif parca.get_param("name", header="content-disposition") == "dosya":
                    dosya_adi = parca.get_filename() or ""
                    dosya_icerigi = parca.get_payload(decode=True)

            row = db.execute("SELECT ad FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone()
            if not row or not dosya_adi:
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("<body style='background:#0f172a;color:white;padding:40px;'><h3>❌ Hata: Geçersiz API Anahtarı veya dosya seçilmedi.</h3><a href='/' style='color:#93c5fd;'>Geri Dön</a></body>".encode())
                return

            guvenli_ad = f"{anahtar}_{os.path.basename(dosya_adi)}"
            with open(os.path.join("dosyalar", guvenli_ad), "wb") as f:
                f.write(dosya_icerigi)
            db.execute("UPDATE musteriler SET dosya_adi=? WHERE anahtar=?", (guvenli_ad, anahtar))
            db.commit()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:40px;'><h2>🚀 Dosya Otoyola Yüklendi!</h2><p><b>{dosya_adi}</b> dağıtıma hazır.</p><a href='/' style='color:#93c5fd;'>← Ana Sayfaya Dön</a></body>".encode())

port = int(os.environ.get("PORT", 8080))
print(f"Veri Otoyolu Canli IBAN Surumu {port} portunda yayinda...")
HTTPServer(("0.0.0.0", port), VeriOtoyoluBulut).serve_forever()
