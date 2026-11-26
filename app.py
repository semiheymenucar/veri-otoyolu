        if p.path == "/indir" or self.headers.get("X-API-Key"):
            k_hedef = key or self.headers.get("X-API-Key")
            row = db.execute("SELECT kalan_hak FROM musteriler WHERE anahtar=?", (k_hedef,)).fetchone()
            if not row: self.html(401, "<h3>Geçersiz Anahtar</h3>"); return
            kalan = 0
            for v in row: kalan = int(v)
            if kalan <= 0:
                log_yaz(ip, "INDIRME_ENGELLENDI", f"{k_hedef} (Kota 0)")
                self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ Kotanız Bitti (0 Hak)!</h3><p><b>100 TL = 100 Hak</b> için IBAN: <code>{IBAN_NO}</code> ({ALICI_AD})<br>Açıklama: <code>{k_hedef}</code></p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
            db.execute("UPDATE musteriler SET kalan_hak=kalan_hak-1, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (k_hedef,)); db.commit()
            log_yaz(ip, "VERI_INDIRILDI", f"{k_hedef} (Kalan: {kalan - 1})")
            self.ham_veri_gonder(k_hedef, True); return
        if p.path == "/kontrol":
            r = db.execute("SELECT ad, kalan_hak, dosya_adi FROM musteriler WHERE anahtar=?", (key,)).fetchone()
            if not r: self.html(200, "<body style='background:#0f172a;color:white;padding:30px;'><h3>❌ Anahtar Bulunamadı</h3><a href='/' style='color:#38bdf8;'>← Geri</a></body>"); return
            ad_p, kalan_p, dosya_p = r
            temiz = (dosya_p or "oyun_yama_v1.pak").replace(key + "_", "")
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>📂 Depo Durumu</h2><p><b>Proje:</b> {ad_p}</p><p><b>Dosya:</b> {temiz}</p><p><b>Kalan Hak:</b> <b>{kalan_p}</b></p><a href='/onizle?anahtar={key}' style='display:inline-block;background:#3b82f6;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;'>👁️ / 🎵 Dosyayı Aç (Gör / Dinle)</a> <a href='/indir?anahtar={key}' style='display:inline-block;background:#10b981;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;margin-left:8px;'>⬇️ İndir</a><br><br><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return

        if p.path == "/":
            ip_kalan = max(0, 10 - ip_kullanim_bul(ip))
            uyari = f"<p style='color:#f87171;'>⚠️ IP adresiniz ({ip}) için 10 ücretsiz anahtar hakkı doldu! <b>100 TL = 100 Hak</b> yükleyin.</p>" if ip_kalan == 0 else f"<p style='color:#34d399;'>🌐 IP Adresiniz: <code>{ip}</code> | Kalan Ücretsiz Anahtar Hakkınız: <b>{ip_kalan} / 10</b></p>"
            self.html(200, sablon.ana_sayfa(uyari, BANKA_ADI, ALICI_AD, IBAN_NO)); return
    def do_POST(self):
        ham = self.rfile.read(int(self.headers.get("Content-Length", 0))); ip = self.ip_bul()
        if self.path == "/kayit":
            ip_kalan = max(0, 10 - ip_kullanim_bul(ip))
            if ip_kalan <= 0:
                log_yaz(ip, "IP_LIMIT_DOLU", "Yeni anahtar engellendi")
                self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ IP ({ip}) İçin 10 Ücretsiz Hak Doldu!</h3><p><b>100 TL = 100 Hak</b> için IBAN: <code>{IBAN_NO}</code> ({ALICI_AD})</p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
            ad = "".join(parse_qs(ham.decode()).get("ad", ["Proje"])); k = "vo_" + uuid.uuid4().hex[:16]
            db.execute("INSERT INTO musteriler VALUES (?, ?, 10, 0, 'oyun_yama_v1.pak', ?)", (k, ad, ip)); db.commit()
            log_yaz(ip, "YENI_KAYIT", f"{ad} ({k}) | Kalan IP hakkı: {ip_kalan - 1}")
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>✅ Anahtarınız: <code>{k}</code></h2><p>Bu anahtarda <b>10</b> kullanım hakkı var. (IP kalan anahtar hakkı: <b>{ip_kalan - 1} / 10</b>)</p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>")
        elif self.path == "/yukle":
            m = BytesParser(policy=default).parsebytes(f"Content-Type: {self.headers.get('Content-Type')}\r\n\r\n".encode() + ham)
            anahtar, d_adi, icerik = "", "", b""
            for part in m.iter_parts():
                if part.get_param("name", header="content-disposition") == "anahtar": anahtar = part.get_content().strip()
                elif part.get_param("name", header="content-disposition") == "dosya": d_adi = part.get_filename() or ""; icerik = part.get_payload(decode=True)
            row = db.execute("SELECT kalan_hak FROM musteriler WHERE anahtar=?", (anahtar,)).fetchone()
            if not row or not d_adi:
                self.html(400, "<body style='background:#0f172a;color:white;padding:30px;'><h3>❌ Geçersiz Anahtar veya Dosya</h3><a href='/' style='color:#38bdf8;'>Geri</a></body>"); return
            kalan = 0
            for v in row: kalan = int(v)
            if kalan <= 0:
                log_yaz(ip, "YUKLEME_ENGELLENDI", f"{anahtar} (Kota 0)")
                self.html(402, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h3>⚠️ Kotanız Bitti (0 Hak)!</h3><p>Yeni dosya yüklemek için <b>100 TL = 100 Hak</b> yükleyin.<br><b>IBAN:</b> <code>{IBAN_NO}</code> ({ALICI_AD})<br><b>Açıklama:</b> <code>{anahtar}</code></p><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body>"); return
            g_ad = f"{anahtar}_{os.path.basename(d_adi)}"
            open(os.path.join("dosyalar", g_ad), "wb").write(icerik)
            db.execute("UPDATE musteriler SET dosya_adi=?, kalan_hak=kalan_hak-1, toplam_gecis=toplam_gecis+1 WHERE anahtar=?", (g_ad, anahtar)); db.commit()
            log_yaz(ip, "DOSYA_YUKLENDI", f"{anahtar} -> {os.path.basename(d_adi)} (Kalan: {kalan - 1})")
            self.html(200, f"<body style='font-family:sans-serif;background:#0f172a;color:white;padding:30px;'><h2>🚀 Dosya Yüklendi! (Kalan Hak: {kalan - 1})</h2><a href='/kontrol?anahtar={anahtar}' style='color:#34d399;font-weight:bold;'>📂 Dosyayı Aç (Gör / Dinle / İndir) →</a></body>")

HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), Otoyol).serve_forever()
