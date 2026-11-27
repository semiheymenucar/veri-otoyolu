from datetime import datetime

def boyut_yaz(b):
    b = int(b or 0)
    if b >= 1024**3: return f"{b / (1024**3):.2f} GB"
    if b >= 1024**2: return f"{b / (1024**2):.1f} MB"
    if b >= 1024: return f"{b / 1024:.1f} KB"
    return f"{b} B"

def dosya_rozeti(dosya_adi):
    ad = (dosya_adi or "").lower()
    if ad.endswith((".mp4", ".webm", ".mov", ".avi", ".mkv")): return "🎬 Video"
    if ad.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")): return "🖼️ Foto"
    if ad.endswith((".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac")): return "🎵 Müzik"
    if ad.endswith((".pak", ".zip", ".rar", ".exe", ".apk", ".iso", ".7z")): return "🎮 Oyun"
    return "📦 Kasa"

def medya_goruntule(key, dosya_adi, bilet=""):
    ad = dosya_adi.lower()
    src = f"/ham?bilet={bilet}"
    if ad.endswith((".mp4", ".webm", ".mov")): return f"<video controls autoplay style='max-width:100%;border-radius:10px;'><source src='{src}'></video>"
    if ad.endswith((".mp3", ".wav", ".ogg", ".m4a")): return f"<audio controls autoplay style='width:100%;'><source src='{src}'></audio>"
    if ad.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")): return f"<img src='{src}' style='max-width:100%;border-radius:10px;'>"
    return "<p style='color:#94a3b8;'>Bu dosya doğrudan indirilebilir.</p>"

def ana_sayfa(uyari, iban_no, alici_ad, qr_b64):
    return f"""<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Veri Otoyolu - Güvenli Oyun & Bulut Kasası</title>
<style>
body {{ font-family:-apple-system,sans-serif; background:#0f172a; color:#f8fafc; max-width:760px; margin:0 auto; padding:20px; }}
.kart {{ background:#1e293b; border:1px solid #334155; border-radius:12px; padding:18px; margin-bottom:18px; }}
input, select {{ width:100%; box-sizing:border-box; padding:11px; margin:6px 0 12px 0; border-radius:8px; border:1px solid #475569; background:#0f172a; color:white; font-size:15px; }}
button {{ background:#10b981; color:white; border:none; padding:12px; border-radius:8px; font-weight:bold; font-size:15px; cursor:pointer; width:100%; }}
table {{ width:100%; border-collapse:collapse; margin-top:10px; font-size:14px; }}
th, td {{ border:1px solid #334155; padding:10px; text-align:center; }}
th {{ background:#0f172a; color:#38bdf8; }}
</style></head><body>
<h1>🚀 Veri Otoyolu <span style="background:#0284c7;padding:3px 8px;border-radius:6px;font-size:12px;">🛡️ Zero-Disk Kasa</span></h1>
<p style="color:#94a3b8;">Oyun yapımcıları ve geliştiriciler için haftalıktan yıllığa süreli koruma seçenekli bulut kasası.</p>

<div class="kart"><h3>1. Ücretsiz Deneme Kasası Aç (50 MB veya 100 MB)</h3>{uyari}
<form method="POST" action="/anahtar_olustur">
  <input type="text" name="proje_adi" placeholder="Proje veya Oyun Adı" required>
  <select name="deneme_mb"><option value="50">🎁 Ücretsiz 50 MB Deneme Kasası (7 Gün)</option><option value="100">🎁 Ücretsiz 100 MB Deneme Kasası (7 Gün)</option></select>
  <button type="submit">🔑 Ücretsiz Kasa Anahtarı Üret</button>
</form></div>

<div class="kart"><h3>2. Dosya Yükle (Zero-Disk Doğrudan Bulut Akışı)</h3>
<form method="POST" action="/yukle">
  <input type="text" name="anahtar" placeholder="Kasa API Anahtarınız (vo_...)" required>
  <input type="file" name="dosya" required>
  <button type="submit" style="background:#3b82f6;">⚡ Dosyayı Güvenli Kasaya Aktar</button>
</form>
<div id="yukleDurum" style="display:none;margin-top:12px;background:#0f172a;padding:12px;border-radius:8px;border:1px solid #38bdf8;">
  <div id="yukleMetin" style="font-size:13px;color:#38bdf8;margin-bottom:6px;">⏳ Tünel açılıyor...</div>
  <div style="width:100%;background:#1e293b;border-radius:6px;height:14px;overflow:hidden;"><div id="yukleBar" style="width:0%;height:100%;background:linear-gradient(90deg,#10b981,#38bdf8);"></div></div>
</div></div>

<div class="kart"><h3>3. Kasamı Aç / İndir ve Kalan Alanı Gör</h3>
<form method="GET" action="/kontrol"><input type="text" name="anahtar" placeholder="Kasa API Anahtarınız (vo_...)" required><button type="submit" style="background:#6366f1;">📂 Kasayı Kontrol Et</button></form></div>

<div class="kart"><h3>4. Kasa Paketleri & Fiyatlandırma (1 GB – 100 GB)</h3>
<table><tr><th>Kapasite</th><th>1 Hafta (7 Gün)</th><th>1 Ay (30 Gün)</th><th>1 Yıl (365 Gün)</th></tr>
<tr><td><b>1 GB Kasa</b></td><td><b>39 TL</b></td><td><b>89 TL</b></td><td><b>399 TL</b></td></tr>
<tr><td><b>10 GB Kasa</b></td><td><b>129 TL</b></td><td><b>299 TL</b></td><td><b>990 TL</b></td></tr>
<tr><td><b>100 GB Kasa</b></td><td><b>490 TL</b></td><td><b>990 TL</b></td><td><b>4.490 TL</b></td></tr></table>
<div style="margin-top:14px;padding:12px;background:#0f172a;border-radius:8px;border:1px solid #334155;">
  <b>{alici_ad}</b><br>IBAN: <code style="color:#34d399;">{iban_no}</code>
  <button type="button" onclick="navigator.clipboard.writeText('{iban_no}');this.innerText='✅ Kopyalandı!';" style="width:auto;padding:5px 10px;font-size:12px;margin-left:8px;">📋 IBAN Kopyala</button>
  <div style="margin-top:12px;text-align:center;"><img src="data:image/png;base64,{qr_b64}" alt="Akbank TR Karekod" style="width:200px;border-radius:8px;background:white;padding:6px;"></div>
  <small style="color:#cbd5e1;display:block;margin-top:8px;">Açıklamaya sadece <b>API anahtarınızı (vo_...)</b> yazın. Paket tutarını gönderdiğinizde <b>GB ve süreniz</b> otomatik tanımlanır.</small>
</div></div>
<script>
document.addEventListener("DOMContentLoaded", function() {{
  const f = document.querySelector('form[action="/yukle"]'); if (!f) return;
  f.addEventListener("submit", async function(e) {{
    e.preventDefault();
    const k = f.querySelector('input[name="anahtar"]').value.trim();
    const d = f.querySelector('input[type="file"]').files.item(0); if (!k || !d) return;
    const dur = document.getElementById("yukleDurum"), met = document.getElementById("yukleMetin"), bar = document.getElementById("yukleBar");
    dur.style.display = "block"; metin.innerText = "🔐 Şifreli kasa tüneli açılıyor...";
    let iRes; try {{ iRes = await fetch("/oturum_ac", {{method:"POST", headers:{{"X-Anahtar":k,"X-Dosya-Adi":encodeURIComponent(d.name),"X-Toplam-Boyut":String(d.size)}}}}); }} catch(err) {{ metin.innerText = "❌ Bağlantı hatası: " + err; return; }}
    if (!iRes.ok) {{ document.open(); document.write(await iRes.text()); document.close(); return; }}
    const info = await iRes.json(), CHUNK = 10*1024*1024; let off = 0, fid = null;
    while (off < d.size) {{
      const end = Math.min(off + CHUNK, d.size), y = Math.round((end / d.size) * 100);
      met.innerText = "⚡ Doğrudan Bulut Kasasına Akıyor: %" + y; bar.style.width = y + "%";
      const pRes = await fetch(info.upload_url, {{method:"PUT", headers:{{"Content-Range":"bytes "+off+"-"+(end-1)+"/"+d.size}}, body:d.slice(off,end)}});
      if (pRes.status === 200 || pRes.status === 201) {{ fid = (await pRes.json()).id; break; }}
      else if (pRes.status !== 308) {{ met.innerText = "❌ Akış kesildi (" + pRes.status + ")"; return; }}
      off = end;
    }}
    met.innerText = "🛡️ Boyut mühürleniyor...";
    const fRes = await fetch("/yukleme_tamamla", {{method:"POST", headers:{{"X-Anahtar":k,"X-Dosya-Adi":encodeURIComponent(d.name),"X-File-Id":fid||""}}}});
    document.open(); document.write(await fRes.text()); document.close();
  }});
}});
</script></body></html>"""

def kokpit(rows, logs, gizli):
    tr = ""
    for k, ad, kota_b, kull_b, bitis_ts, dosya, m_ip in rows:
        gun = max(0, int((int(bitis_ts or 0) - int(datetime.now().timestamp())) / 86400))
        kad = (dosya or "Dosya yok").split(":")[-1].replace(k + "_", "")
        tr += f"<tr><td>{ad}</td><td><code style='word-break:break-all;'>{k}</code></td><td>{m_ip}</td><td><b>{boyut_yaz(kull_b)} / {boyut_yaz(kota_b)}</b><br><small style='color:#34d399;'>⏳ {gun} gün</small></td><td>{dosya_rozeti(kad)} {kad}</td><td style='white-space:nowrap;'><a href='/onizle?anahtar={k}&admin={gizli}' target='_blank' style='background:#0284c7;color:white;padding:5px 8px;border-radius:6px;text-decoration:none;'>👁️ Bak</a> <form method='GET' action='/yonetim' style='display:inline;'><input type='hidden' name='sifre' value='{gizli}'><input type='hidden' name='ekle' value='{k}'><select name='gb' style='width:auto;padding:3px;'><option value='1'>1 GB</option><option value='10'>10 GB</option><option value='100'>100 GB</option></select><select name='gun' style='width:auto;padding:3px;'><option value='7'>7 Gün</option><option value='30'>30 Gün</option><option value='365'>365 Gün</option></select><button type='submit' style='width:auto;padding:4px 8px;font-size:12px;'>Tanımla</button></form></td></tr>"
    ltr = "".join([f"<tr><td>{z}</td><td><code>{l_ip}</code></td><td><b>{isl}</b></td><td>{det}</td></tr>" for z, l_ip, isl, det in logs])
    return f"<!DOCTYPE html><html lang='tr'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><meta http-equiv='refresh' content='15'><title>Kokpit</title></head><body style='font-family:-apple-system,sans-serif;background:#0f172a;color:white;padding:16px;'><h2>🎛️ Veri Otoyolu Kasa Kokpiti</h2><div style='overflow-x:auto;border:1px solid #334155;border-radius:8px;'><table cellpadding='8' style='border-collapse:collapse;width:100%;font-size:14px;'><tr style='background:#1e293b;'><th>Proje</th><th>Anahtar</th><th>IP</th><th>Kasa & Süre</th><th>Dosya</th><th>İşlem</th></tr>{tr}</table></div><h3>📜 Güvenlik Günlüğü</h3><div style='overflow-x:auto;border:1px solid #334155;border-radius:8px;'><table cellpadding='8' style='border-collapse:collapse;width:100%;font-size:14px;'><tr style='background:#1e293b;'><th>Zaman</th><th>IP</th><th>İşlem</th><th>Detay</th></tr>{ltr}</table></div><br><a href='/' style='color:#38bdf8;'>← Ana Sayfa</a></body></html>"
