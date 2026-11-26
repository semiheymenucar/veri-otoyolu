def kokpit_html(db, sifre):
    rows = db.execute("SELECT anahtar, ad, kalan_hak, toplam_gecis, dosya_adi FROM musteriler").fetchall()
    satirlar = ""
    for anahtar, ad, kalan, gecis, dosya in rows:
        temiz = (dosya or "oyun_yama_v1.pak").replace(anahtar + "_", "")
        satirlar += f"<tr><td>{ad}</td><td><code>{anahtar}</code></td><td>{kalan}</td><td>{gecis}</td><td>{temiz}</td><td><a href='/onizle?anahtar={anahtar}' target='_blank' style='color:#38bdf8;margin-right:10px;'>👁️ Gör</a><a href='/yonetim?sifre={sifre}&ekle={anahtar}' style='color:#10b981;'>+1000 Hak</a></td></tr>"
    return f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:24px;'><h2>🎛️ Veri Otoyolu Kokpit</h2><table border='1' cellpadding='10' style='border-collapse:collapse;width:100%;border-color:#334155;'><tr><th>Proje</th><th>Anahtar</th><th>Kalan</th><th>Geçiş</th><th>Dosya</th><th>İşlem</th></tr>{satirlar}</table><br><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"
