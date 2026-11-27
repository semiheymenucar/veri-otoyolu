from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# Müşteriler ve kalan veri geçiş hakları (Otomatik Gişe Veritabanı)
MUSTERILER = {
    "anahtar_oyun_studyo_1": {"ad": "Indie Oyun Ekibi", "kalan_hak": 5, "toplam_gecis": 0},
    "anahtar_uygulama_2": {"ad": "AI Mobil App", "kalan_hak": 100, "toplam_gecis": 0}
}

class VeriOtoyolu(BaseHTTPRequestHandler):
    def do_GET(self):
        api_key = self.headers.get("X-API-Key")
        
        # 1. Geçiş Kartı (API Anahtarı) Kontrolü
        if api_key not in MUSTERILER:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(json.dumps({"hata": "Gecersiz API Anahtari! Gise kapali."}).encode())
            return

        musteri = MUSTERILER[api_key]

        # 2. Kota / Bakiye Kontrolü
        if musteri["kalan_hak"] <= 0:
            self.send_response(402)
            self.end_headers()
            self.wfile.write(json.dumps({"hata": "Kotaniz bitti! Otomatik odeme yapin."}).encode())
            return

        # 3. Veri Geçişine İzin Ver ve Sayacı Güncelle
        musteri["kalan_hak"] -= 1
        musteri["toplam_gecis"] += 1

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        cevap = {
            "durum": "Veri basariyla ulastirildi",
            "musteri": musteri["ad"],
            "kalan_hak": musteri["kalan_hak"],
            "toplam_gecis": musteri["toplam_gecis"]
        }
        self.wfile.write(json.dumps(cevap).encode())

print("Veri Otoyolu Motoru 8080 portunda calisiyor...")
HTTPServer(("127.0.0.1", 8080), VeriOtoyolu).serve_forever()
