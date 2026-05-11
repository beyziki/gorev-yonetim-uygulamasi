"""
╔══════════════════════════════════════════════════════════╗
║         GÖREV YÖNETİM UYGULAMASI (To-Do List)           ║
║         Geliştirici: TNC Group Staj Projesi              ║
╚══════════════════════════════════════════════════════════╝

Bu uygulama, kullanıcının görevlerini eklemesine, görüntülemesine,
düzenlemesine, silmesine ve yönetmesine olanak tanır.

Özellikler:
  - Görev ekleme, listeleme, düzenleme, silme
  - Tamamlandı/tamamlanmadı durumu takibi
  - Öncelik seviyesi atama (Düşük, Orta, Yüksek, Kritik)
  - Son tarih belirleme
  - Görev arama
  - Çeşitli kriterlere göre sıralama
  - İstatistik ekranı
  - JSON tabanlı kalıcı veri depolama
  - Renkli konsol arayüzü
"""

import json
import os
import sys
from datetime import datetime, date

# ─────────────────────────────────────────────
# RENK TANIMLARI (ANSI escape kodları)
# Google Colab ve çoğu terminal destekler.
# ─────────────────────────────────────────────
class Renk:
    SIFIRLA    = "\033[0m"
    KALIN      = "\033[1m"
    KIRMIZI    = "\033[91m"
    YESIL      = "\033[92m"
    SARI       = "\033[93m"
    MAVI       = "\033[94m"
    MAGENTA    = "\033[95m"
    CYAN       = "\033[96m"
    BEYAZ      = "\033[97m"
    GRI        = "\033[90m"
    BG_KIRMIZI = "\033[41m"
    BG_YESIL   = "\033[42m"


# ─────────────────────────────────────────────
# SABİTLER
# ─────────────────────────────────────────────
DOSYA_ADI = "gorevler.json"

ONCELIK_SEVIYELERI = {
    "1": "Düşük",
    "2": "Orta",
    "3": "Yüksek",
    "4": "Kritik"
}

ONCELIK_RENKLERI = {
    "Düşük":   Renk.GRI,
    "Orta":    Renk.CYAN,
    "Yüksek":  Renk.SARI,
    "Kritik":  Renk.KIRMIZI
}

DURUM_SEMBOLU = {
    True:  f"{Renk.YESIL}✓{Renk.SIFIRLA}",   # Tamamlandı
    False: f"{Renk.GRI}○{Renk.SIFIRLA}"       # Bekliyor
}


# ─────────────────────────────────────────────
# YARDIMCI YAZDIRMA FONKSİYONLARI
# ─────────────────────────────────────────────
def baslik_yazdir(metin: str):
    """Renkli başlık yazar."""
    genislik = 60
    print(f"\n{Renk.MAVI}{Renk.KALIN}{'─' * genislik}{Renk.SIFIRLA}")
    print(f"{Renk.MAVI}{Renk.KALIN}  {metin}{Renk.SIFIRLA}")
    print(f"{Renk.MAVI}{Renk.KALIN}{'─' * genislik}{Renk.SIFIRLA}")


def basari_yazdir(metin: str):
    """Yeşil başarı mesajı yazar."""
    print(f"{Renk.YESIL}✓ {metin}{Renk.SIFIRLA}")


def hata_yazdir(metin: str):
    """Kırmızı hata mesajı yazar."""
    print(f"{Renk.KIRMIZI}✗ {metin}{Renk.SIFIRLA}")


def bilgi_yazdir(metin: str):
    """Sarı bilgi mesajı yazar."""
    print(f"{Renk.SARI}ℹ {metin}{Renk.SIFIRLA}")


def ayirici_yazdir():
    """İnce ayırıcı çizgi yazar."""
    print(f"{Renk.GRI}{'─' * 60}{Renk.SIFIRLA}")


# ─────────────────────────────────────────────
# DOSYA İŞLEMLERİ
# ─────────────────────────────────────────────
def gorevleri_yukle() -> list:
    """
    Görevleri JSON dosyasından okur.
    Dosya yoksa veya bozuksa boş liste döndürür.
    """
    try:
        with open(DOSYA_ADI, "r", encoding="utf-8") as dosya:
            gorevler = json.load(dosya)
            basari_yazdir("Görevler başarıyla yüklendi.")
            return gorevler
    except FileNotFoundError:
        bilgi_yazdir("Görev dosyası bulunamadı. Yeni bir liste oluşturuldu.")
        return []
    except json.JSONDecodeError:
        hata_yazdir("Görev dosyası bozuk. Yeni bir liste başlatılıyor.")
        return []
    except IOError as e:
        hata_yazdir(f"Dosya okuma hatası: {e}")
        return []


def gorevleri_kaydet(gorevler: list) -> bool:
    """
    Görevleri JSON dosyasına yazar.
    Başarı durumuna göre True/False döndürür.
    """
    try:
        with open(DOSYA_ADI, "w", encoding="utf-8") as dosya:
            json.dump(gorevler, dosya, ensure_ascii=False, indent=4)
        basari_yazdir("Görevler başarıyla kaydedildi.")
        return True
    except IOError as e:
        hata_yazdir(f"Dosya yazma hatası: {e}")
        return False
    except Exception as e:
        hata_yazdir(f"Beklenmeyen hata: {e}")
        return False


# ─────────────────────────────────────────────
# GÖREV OLUŞTURMA YARDIMCISI
# ─────────────────────────────────────────────
def yeni_gorev_nesnesi_olustur(baslik: str, oncelik: str = "Orta",
                                son_tarih: str = None) -> dict:
    """
    Standart görev sözlüğü oluşturur.
    Her görev: id, baslik, tamamlandi, oncelik, son_tarih, olusturma_tarihi
    """
    return {
        "id": int(datetime.now().timestamp() * 1000),  # Benzersiz ID
        "baslik": baslik.strip(),
        "tamamlandi": False,
        "oncelik": oncelik,
        "son_tarih": son_tarih,  # "YYYY-MM-DD" formatı veya None
        "olusturma_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
    }


# ─────────────────────────────────────────────
# GÖREV GÖRÜNTÜLEME
# ─────────────────────────────────────────────
def gorev_satiri_yazdir(indeks: int, gorev: dict):
    """
    Tek bir görevi biçimlendirilmiş şekilde yazar.
    """
    numara     = f"{Renk.BEYAZ}{Renk.KALIN}{indeks:2}.{Renk.SIFIRLA}"
    durum      = DURUM_SEMBOLU[gorev["tamamlandi"]]
    oncelik    = gorev.get("oncelik", "Orta")
    renk       = ONCELIK_RENKLERI.get(oncelik, Renk.BEYAZ)
    oncelik_et = f"{renk}[{oncelik:7}]{Renk.SIFIRLA}"

    # Son tarih: geçmiş tarihse kırmızıyla göster
    son_tarih = gorev.get("son_tarih")
    if son_tarih:
        try:
            son_dt = datetime.strptime(son_tarih, "%Y-%m-%d").date()
            bugün = date.today()
            if son_dt < bugün and not gorev["tamamlandi"]:
                tarih_str = f"{Renk.KIRMIZI}⚠ {son_tarih}{Renk.SIFIRLA}"
            elif son_dt == bugün and not gorev["tamamlandi"]:
                tarih_str = f"{Renk.SARI}⏰ {son_tarih}{Renk.SIFIRLA}"
            else:
                tarih_str = f"{Renk.GRI}{son_tarih}{Renk.SIFIRLA}"
        except ValueError:
            tarih_str = f"{Renk.GRI}{son_tarih}{Renk.SIFIRLA}"
    else:
        tarih_str = f"{Renk.GRI}Tarih yok{Renk.SIFIRLA}"

    # Tamamlanan görevleri soluk göster
    if gorev["tamamlandi"]:
        baslik = f"{Renk.GRI}{gorev['baslik']}{Renk.SIFIRLA}"
    else:
        baslik = f"{Renk.BEYAZ}{gorev['baslik']}{Renk.SIFIRLA}"

    print(f"  {numara} {durum} {oncelik_et} {baslik}")
    print(f"         {Renk.GRI}📅 {tarih_str}  "
          f"🕐 {gorev.get('olusturma_tarihi', '-')}{Renk.SIFIRLA}")


# ─────────────────────────────────────────────
# ANA FONKSİYONLAR
# ─────────────────────────────────────────────
def gorevleri_listele(gorevler: list, sirali_gorevler: list = None):
    """
    Görev listesini ekrana yazar.
    sirali_gorevler verilirse onu listeler (sıralama için).
    """
    baslik_yazdir("GÖREV LİSTESİ")

    liste = sirali_gorevler if sirali_gorevler is not None else gorevler

    if not liste:
        bilgi_yazdir("Henüz görev bulunmamaktadır.")
        return

    tamamlanan = sum(1 for g in liste if g["tamamlandi"])
    bekleyen   = len(liste) - tamamlanan

    print(f"  {Renk.YESIL}Tamamlanan: {tamamlanan}{Renk.SIFIRLA}  "
          f"{Renk.CYAN}Bekleyen: {bekleyen}{Renk.SIFIRLA}  "
          f"{Renk.BEYAZ}Toplam: {len(liste)}{Renk.SIFIRLA}\n")

    for i, gorev in enumerate(liste, start=1):
        gorev_satiri_yazdir(i, gorev)
        if i < len(liste):
            print()

    ayirici_yazdir()


def gorev_ekle(gorevler: list):
    """
    Kullanıcıdan yeni görev bilgilerini alır ve listeye ekler.
    """
    baslik_yazdir("YENİ GÖREV EKLE")

    # --- Görev başlığı ---
    while True:
        baslik = input(f"  {Renk.CYAN}Görev başlığı: {Renk.SIFIRLA}").strip()
        if baslik:
            break
        hata_yazdir("Görev başlığı boş olamaz! Lütfen tekrar girin.")

    # --- Öncelik seviyesi ---
    print(f"\n  {Renk.BEYAZ}Öncelik seviyesi:{Renk.SIFIRLA}")
    for k, v in ONCELIK_SEVIYELERI.items():
        renk = ONCELIK_RENKLERI[v]
        print(f"    {k}. {renk}{v}{Renk.SIFIRLA}")

    while True:
        oncelik_secim = input(
            f"  {Renk.CYAN}Seçiminiz (1-4, varsayılan 2=Orta): {Renk.SIFIRLA}"
        ).strip()
        if oncelik_secim == "":
            oncelik = "Orta"
            break
        if oncelik_secim in ONCELIK_SEVIYELERI:
            oncelik = ONCELIK_SEVIYELERI[oncelik_secim]
            break
        hata_yazdir("Lütfen 1-4 arasında bir değer girin!")

    # --- Son tarih ---
    while True:
        son_tarih_girdi = input(
            f"\n  {Renk.CYAN}Son tarih (YYYY-AA-GG, boş bırakabilirsiniz): {Renk.SIFIRLA}"
        ).strip()
        if son_tarih_girdi == "":
            son_tarih = None
            break
        try:
            datetime.strptime(son_tarih_girdi, "%Y-%m-%d")
            son_tarih = son_tarih_girdi
            break
        except ValueError:
            hata_yazdir("Geçersiz tarih formatı! Örnek: 2025-12-31")

    # Görevi oluştur ve listeye ekle
    yeni_gorev = yeni_gorev_nesnesi_olustur(baslik, oncelik, son_tarih)
    gorevler.append(yeni_gorev)

    print()
    basari_yazdir(f"'{baslik}' görevi eklendi.")
    gorevleri_kaydet(gorevler)


def gorev_sil(gorevler: list):
    """
    Kullanıcının belirttiği numaralı görevi listeden siler.
    """
    baslik_yazdir("GÖREV SİL")

    if not gorevler:
        bilgi_yazdir("Silinecek görev bulunmamaktadır.")
        return

    gorevleri_listele(gorevler)

    while True:
        girdi = input(
            f"\n  {Renk.CYAN}Silmek istediğiniz görevin numarası "
            f"(iptal için 0): {Renk.SIFIRLA}"
        ).strip()
        try:
            numara = int(girdi)
        except ValueError:
            hata_yazdir("Lütfen bir sayı girin!")
            continue

        if numara == 0:
            bilgi_yazdir("Silme işlemi iptal edildi.")
            return
        if 1 <= numara <= len(gorevler):
            silinen = gorevler.pop(numara - 1)
            basari_yazdir(f"'{silinen['baslik']}' görevi silindi.")
            gorevleri_kaydet(gorevler)
            return
        hata_yazdir(f"Geçersiz görev numarası! (1-{len(gorevler)} arasında girin)")


def gorev_duzenle(gorevler: list):
    """
    Kullanıcının seçtiği görevi düzenler.
    Başlık, öncelik ve son tarih güncellenebilir.
    """
    baslik_yazdir("GÖREV DÜZENLE")

    if not gorevler:
        bilgi_yazdir("Düzenlenecek görev bulunmamaktadır.")
        return

    gorevleri_listele(gorevler)

    while True:
        girdi = input(
            f"\n  {Renk.CYAN}Düzenlemek istediğiniz görevin numarası "
            f"(iptal için 0): {Renk.SIFIRLA}"
        ).strip()
        try:
            numara = int(girdi)
        except ValueError:
            hata_yazdir("Lütfen bir sayı girin!")
            continue

        if numara == 0:
            bilgi_yazdir("Düzenleme işlemi iptal edildi.")
            return
        if 1 <= numara <= len(gorevler):
            break
        hata_yazdir(f"Geçersiz görev numarası! (1-{len(gorevler)} arasında girin)")

    gorev = gorevler[numara - 1]

    print(f"\n  {Renk.GRI}(Değiştirmek istemediğiniz alanları boş bırakın){Renk.SIFIRLA}")

    # --- Yeni başlık ---
    yeni_baslik = input(
        f"  {Renk.CYAN}Yeni başlık [{gorev['baslik']}]: {Renk.SIFIRLA}"
    ).strip()

    # --- Yeni öncelik ---
    print(f"\n  {Renk.BEYAZ}Yeni öncelik (mevcut: "
          f"{ONCELIK_RENKLERI[gorev['oncelik']]}{gorev['oncelik']}"
          f"{Renk.SIFIRLA}):{Renk.SIFIRLA}")
    for k, v in ONCELIK_SEVIYELERI.items():
        renk = ONCELIK_RENKLERI[v]
        print(f"    {k}. {renk}{v}{Renk.SIFIRLA}")

    yeni_oncelik_secim = input(
        f"  {Renk.CYAN}Seçiminiz (boş bırakın = değiştirme): {Renk.SIFIRLA}"
    ).strip()

    # --- Yeni son tarih ---
    mevcut_tarih = gorev.get("son_tarih") or "yok"
    while True:
        yeni_tarih_girdi = input(
            f"\n  {Renk.CYAN}Yeni son tarih [{mevcut_tarih}] "
            f"(boş bırakın = değiştirme, 'sil' = tarihi kaldır): {Renk.SIFIRLA}"
        ).strip()
        if yeni_tarih_girdi == "" or yeni_tarih_girdi.lower() == "sil":
            break
        try:
            datetime.strptime(yeni_tarih_girdi, "%Y-%m-%d")
            break
        except ValueError:
            hata_yazdir("Geçersiz tarih formatı! Örnek: 2025-12-31")

    # Değişiklikleri uygula
    degisiklik_var = False

    if yeni_baslik:
        gorev["baslik"] = yeni_baslik
        degisiklik_var = True

    if yeni_oncelik_secim in ONCELIK_SEVIYELERI:
        gorev["oncelik"] = ONCELIK_SEVIYELERI[yeni_oncelik_secim]
        degisiklik_var = True

    if yeni_tarih_girdi.lower() == "sil":
        gorev["son_tarih"] = None
        degisiklik_var = True
    elif yeni_tarih_girdi != "":
        gorev["son_tarih"] = yeni_tarih_girdi
        degisiklik_var = True

    if degisiklik_var:
        print()
        basari_yazdir("Görev başarıyla güncellendi.")
        gorevleri_kaydet(gorevler)
    else:
        bilgi_yazdir("Hiçbir değişiklik yapılmadı.")


def gorev_durumu_degistir(gorevler: list):
    """
    Görevin tamamlandı/tamamlanmadı durumunu değiştirir.
    """
    baslik_yazdir("GÖREV DURUMU DEĞİŞTİR")

    if not gorevler:
        bilgi_yazdir("Görev bulunmamaktadır.")
        return

    gorevleri_listele(gorevler)

    while True:
        girdi = input(
            f"\n  {Renk.CYAN}Durumunu değiştirmek istediğiniz görevin numarası "
            f"(iptal için 0): {Renk.SIFIRLA}"
        ).strip()
        try:
            numara = int(girdi)
        except ValueError:
            hata_yazdir("Lütfen bir sayı girin!")
            continue

        if numara == 0:
            bilgi_yazdir("İşlem iptal edildi.")
            return
        if 1 <= numara <= len(gorevler):
            break
        hata_yazdir(f"Geçersiz görev numarası! (1-{len(gorevler)} arasında girin)")

    gorev = gorevler[numara - 1]
    gorev["tamamlandi"] = not gorev["tamamlandi"]
    yeni_durum = "Tamamlandı ✓" if gorev["tamamlandi"] else "Bekliyor ○"
    print()
    basari_yazdir(f"'{gorev['baslik']}' → {yeni_durum}")
    gorevleri_kaydet(gorevler)


def gorev_ara(gorevler: list):
    """
    Görev başlıklarında anahtar kelime araması yapar.
    """
    baslik_yazdir("GÖREV ARA")

    if not gorevler:
        bilgi_yazdir("Görev listesi boş.")
        return

    arama = input(
        f"  {Renk.CYAN}Aranacak kelime: {Renk.SIFIRLA}"
    ).strip().lower()

    if not arama:
        hata_yazdir("Arama terimi boş olamaz!")
        return

    sonuclar = [g for g in gorevler if arama in g["baslik"].lower()]

    if sonuclar:
        basari_yazdir(f"'{arama}' için {len(sonuclar)} sonuç bulundu:")
        gorevleri_listele(gorevler, sirali_gorevler=sonuclar)
    else:
        bilgi_yazdir(f"'{arama}' için sonuç bulunamadı.")


def gorevleri_sirala(gorevler: list):
    """
    Görev listesini çeşitli kriterlere göre sıralar ve gösterir.
    """
    baslik_yazdir("GÖREVLERİ SIRALA")

    if not gorevler:
        bilgi_yazdir("Sıralanacak görev bulunmamaktadır.")
        return

    print(f"  {Renk.BEYAZ}Sıralama kriteri:{Renk.SIFIRLA}")
    print(f"    {Renk.CYAN}1.{Renk.SIFIRLA} Önceliğe göre (Kritik → Düşük)")
    print(f"    {Renk.CYAN}2.{Renk.SIFIRLA} Son tarihe göre (En yakın önce)")
    print(f"    {Renk.CYAN}3.{Renk.SIFIRLA} Duruma göre (Bekleyenler önce)")
    print(f"    {Renk.CYAN}4.{Renk.SIFIRLA} Oluşturma tarihine göre (En yeni önce)")
    print(f"    {Renk.CYAN}5.{Renk.SIFIRLA} Alfabetik (A → Z)")

    secim = input(f"\n  {Renk.CYAN}Seçiminiz (1-5): {Renk.SIFIRLA}").strip()

    oncelik_sirasi = {"Kritik": 0, "Yüksek": 1, "Orta": 2, "Düşük": 3}

    if secim == "1":
        sirali = sorted(gorevler,
                        key=lambda g: oncelik_sirasi.get(g["oncelik"], 99))
        baslik_yazdir("ÖNCELIĞE GÖRE SIRALANDI")

    elif secim == "2":
        sirali = sorted(gorevler,
                        key=lambda g: (g["son_tarih"] is None,
                                       g["son_tarih"] or "9999-99-99"))
        baslik_yazdir("SON TARİHE GÖRE SIRALANDI")

    elif secim == "3":
        sirali = sorted(gorevler, key=lambda g: g["tamamlandi"])
        baslik_yazdir("DURUMA GÖRE SIRALANDI")

    elif secim == "4":
        sirali = sorted(gorevler,
                        key=lambda g: g.get("olusturma_tarihi", ""),
                        reverse=True)
        baslik_yazdir("OLUŞTURMA TARİHİNE GÖRE SIRALANDI")

    elif secim == "5":
        sirali = sorted(gorevler, key=lambda g: g["baslik"].lower())
        baslik_yazdir("ALFABETİK SIRALANDI")

    else:
        hata_yazdir("Geçersiz seçim!")
        return

    gorevleri_listele(gorevler, sirali_gorevler=sirali)


def istatistikleri_goster(gorevler: list):
    """
    Görev listesi hakkında özet istatistikler gösterir.
    """
    baslik_yazdir("İSTATİSTİKLER")

    toplam     = len(gorevler)
    tamamlanan = sum(1 for g in gorevler if g["tamamlandi"])
    bekleyen   = toplam - tamamlanan

    if toplam == 0:
        bilgi_yazdir("Henüz görev eklenmemiş.")
        return

    yuzde = (tamamlanan / toplam * 100) if toplam > 0 else 0

    # İlerleme çubuğu
    bar_uzunluk  = 30
    dolu         = int(bar_uzunluk * yuzde / 100)
    bos          = bar_uzunluk - dolu
    ilerleme_bar = (f"{Renk.YESIL}{'█' * dolu}"
                    f"{Renk.GRI}{'░' * bos}{Renk.SIFIRLA}")

    print(f"  {Renk.BEYAZ}Toplam Görev   : {Renk.CYAN}{toplam}{Renk.SIFIRLA}")
    print(f"  {Renk.BEYAZ}Tamamlanan     : {Renk.YESIL}{tamamlanan}{Renk.SIFIRLA}")
    print(f"  {Renk.BEYAZ}Bekleyen       : {Renk.SARI}{bekleyen}{Renk.SIFIRLA}")
    print(f"  {Renk.BEYAZ}Tamamlanma     : {ilerleme_bar} "
          f"{Renk.CYAN}{yuzde:.1f}%{Renk.SIFIRLA}")

    # Öncelik dağılımı
    print(f"\n  {Renk.BEYAZ}── Öncelik Dağılımı ──{Renk.SIFIRLA}")
    for seviye in ["Kritik", "Yüksek", "Orta", "Düşük"]:
        sayi  = sum(1 for g in gorevler if g.get("oncelik") == seviye)
        renk  = ONCELIK_RENKLERI[seviye]
        bar   = "■" * sayi
        print(f"  {renk}{seviye:8}{Renk.SIFIRLA} : {renk}{bar}{Renk.SIFIRLA} {sayi}")

    # Gecikmiş görevler
    bugun = date.today()
    gecikmis = [
        g for g in gorevler
        if g.get("son_tarih") and not g["tamamlandi"]
        and datetime.strptime(g["son_tarih"], "%Y-%m-%d").date() < bugun
    ]
    if gecikmis:
        print(f"\n  {Renk.KIRMIZI}⚠ Gecikmiş Görevler: {len(gecikmis)}{Renk.SIFIRLA}")
        for g in gecikmis:
            print(f"    {Renk.KIRMIZI}• {g['baslik']} "
                  f"({g['son_tarih']}){Renk.SIFIRLA}")

    ayirici_yazdir()


# ─────────────────────────────────────────────
# ANA MENÜ
# ─────────────────────────────────────────────
def ana_menu_yazdir():
    """Ana menüyü renkli olarak ekrana yazar."""
    print(f"\n{Renk.MAVI}{Renk.KALIN}{'═' * 60}{Renk.SIFIRLA}")
    print(f"{Renk.MAVI}{Renk.KALIN}{'  TO-DO LIST UYGULAMASI':^60}{Renk.SIFIRLA}")
    print(f"{Renk.MAVI}{Renk.KALIN}{'═' * 60}{Renk.SIFIRLA}")

    seçenekler = [
        ("1", "📋", "Görevleri Listele",         Renk.CYAN),
        ("2", "➕", "Yeni Görev Ekle",            Renk.YESIL),
        ("3", "✏️ ", "Görev Düzenle",             Renk.SARI),
        ("4", "🗑️ ", "Görev Sil",                Renk.KIRMIZI),
        ("5", "✅", "Görev Durumu Değiştir",      Renk.YESIL),
        ("6", "🔍", "Görev Ara",                  Renk.CYAN),
        ("7", "🔃", "Görevleri Sırala",           Renk.MAGENTA),
        ("8", "📊", "İstatistikler",              Renk.MAGENTA),
        ("9", "🚪", "Çıkış",                      Renk.GRI),
    ]
    for num, sembol, metin, renk in seçenekler:
        print(f"  {renk}{num}.{Renk.SIFIRLA} {sembol}  {renk}{metin}{Renk.SIFIRLA}")

    print(f"{Renk.MAVI}{'─' * 60}{Renk.SIFIRLA}")


def ana_program():
    """
    Uygulamanın ana döngüsü.
    Menüyü gösterir, kullanıcı seçimini alır ve ilgili fonksiyonu çalıştırır.
    """
    # Karşılama ekranı
    print(f"\n{Renk.CYAN}{Renk.KALIN}")
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║       GÖREV YÖNETİM UYGULAMASINA HOŞ GELDİNİZ! ║")
    print("  ║            TNC Group Staj Projesi 2025          ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print(Renk.SIFIRLA)

    # Görevleri dosyadan yükle
    gorevler = gorevleri_yukle()

    # Ana döngü
    while True:
        ana_menu_yazdir()

        secim = input(
            f"  {Renk.CYAN}{Renk.KALIN}Seçiminiz (1-9): {Renk.SIFIRLA}"
        ).strip()

        if secim == "1":
            gorevleri_listele(gorevler)

        elif secim == "2":
            gorev_ekle(gorevler)

        elif secim == "3":
            gorev_duzenle(gorevler)

        elif secim == "4":
            gorev_sil(gorevler)

        elif secim == "5":
            gorev_durumu_degistir(gorevler)

        elif secim == "6":
            gorev_ara(gorevler)

        elif secim == "7":
            gorevleri_sirala(gorevler)

        elif secim == "8":
            istatistikleri_goster(gorevler)

        elif secim == "9":
            print(f"\n{Renk.CYAN}Programdan çıkılıyor... "
                  f"Görüşmek üzere! 👋{Renk.SIFIRLA}\n")
            break

        else:
            hata_yazdir("Geçersiz seçim! Lütfen 1-9 arasında bir değer girin.")

        # Her işlem sonrası devam için bekle
        input(f"\n  {Renk.GRI}[Devam etmek için Enter'a basın...]{Renk.SIFIRLA}")


# ─────────────────────────────────────────────
# PROGRAMI BAŞLAT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    ana_program()
