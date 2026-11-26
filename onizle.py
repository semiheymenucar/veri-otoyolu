import os
def dosya_onizle(handler, db, key):
    r = db.execute("SELECT dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
    if not r:
        handler.gonder_html(404, "<body style='background:#0f172a;color:white;padding:30px;'><h3>Dosya Bulunamadi</h3></body>")
        return
    yol = os.path.join("dosyalar", r or "oyun_yama_v1.pak")
    if not os.path.exists(yol):
        yol = "dosyalar/oyun_yama_v1.pak"
    ad = yol.lower()
    tur = "image/jpeg" if ad.endswith((".jpg",".jpeg")) else "image/png" if ad.endswith(".png") else "image/webp" if ad.endswith(".webp") else "application/pdf" if ad.endswith(".pdf") else "text/plain; charset=utf-8"
    veri = open(yol, "rb").read()
    handler.send_response(200)
    handler.send_header("Content-Type", tur)
    handler.send_header("Content-Length", str(len(veri)))
    handler.send_header("Content-Disposition", "inline")
    handler.end_headers()
    handler.wfile.write(veri)
