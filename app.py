from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3, json, os

db = sqlite3.connect("otoyol.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS musteriler (anahtar TEXT PRIMARY KEY, ad TEXT, kalan_hak INTEGER, toplam_gecis INTEGER)")
db.execute("INSERT OR IGNORE INTO musteriler VALUES ('anahtar_oyun_studyo_1', 'Indie Oyun Ekibi', 5, 0)")
db.commit()

os.makedirs("dosyalar", exist_ok=True)
with open("dosyalar/oyun_yama_v1.pak", "wb") as f:
    f.write(b"GERCEK_OYUN_VERI_PAKETI_ICERIGI_10010101" * 250)

class VeriOtoyoluBulut(BaseHTTPRequestHandler):
    def do_GET(self):
        # Ana sayfaya tarayıcıdan girenler için sistem tanıtım mesajı
        if self.path == "/" and not self.headers.get("X-API-Key"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h1>Veri Otoyolu API Aktif</h1><p>Veri cekmek icin X-API-Key basligi ile istek atin.</p>".encode())
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
            self.wfile.write(json.dumps({"hata": "Kotaniz bitti! Otomatik odeme gerekli."}).encode())
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

port = int(os.environ.get("PORT", 8080))
print(f"Veri Otoyolu Bulut Motoru {port} portunda yayinda...")
HTTPServer(("0.0.0.0", port), VeriOtoyoluBulut).serve_forever()
