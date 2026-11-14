"""Build the real-connection user bundle without simulator or synthetic samples."""

import argparse
from pathlib import Path
import zipfile


def package(output):
    root = Path(__file__).resolve().parents[1]
    files = [root / name for name in ('BimmerTool.py', 'Mac-Baslat.command', 'Windows-Baslat.bat')]
    files += [path for path in sorted((root / 'bimmertool').glob('*.py')) if path.name != 'simulator.py']
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, 'BimmerTool/' + str(path.relative_to(root)))
        archive.writestr('BimmerTool/ONCE-OKU.txt', '''BIMMERTOOL - GERCEK BAGLANTI SURUMU 0.16.0
Mac: ZIP'i acin, BimmerTool/Mac-Baslat.command dosyasina cift tiklayin.
Python 3.10+ ve Tkinter gerekir. Windows: Windows-Baslat.bat.
Moduller: 0x00-0xFF adres taramasi, ilerleme ve durdurma. Kismi sonuc tum arac taramasi degildir.
Hata kodlari -> Secili kaydin durum ayrintisi: gercek okuma status baytinin 8 bitini aciklar, ariza nedeni uydurmaz.
Dosya araclari -> Iki FA XML karsilastir: standardFA ve saCode farklari. Yerel dosya islemidir, araca yazmaz.
Bu pakette simulator, sahte olcum veya ornek kodlama adresi bulunmaz.
Uygulamada gizli demo acma parametresi veya simulator baslatma metodu yoktur.
ENET ile kendi araciniza baglanin. Once VIN, modul kimligi ve salt okunur saglik kontrolunu deneyin.
Gercek ix40 ve macOS uzerinde dogrulanmamistir. Desteklenen protokoller HSFZ/DoIP.
HU_MGU4 FDL/NCD yazma ve gercek BMW batarya/sarj tanimlari mevcut degildir.
EV olcumleri icin araciniza uygun dogrulanmis olcum profili gerekir. Yoksa degerler bos kalir.
DID yazma genel uzman aracidir; BMW ozellik kodlamasinin yerine gecmez.
Yazmadan once tanimi dogrulayin; yanlis veri modulun calismasini bozabilir.
Yedek, VIN eslestirme ve onay kontrolleri korunmustur. Tam ECU kurtarma destegi yoktur.
Canli izlemeyi durdurup Baglantiyi kes dugmesiyle oturum verilerini temizleyebilirsiniz.
Yeni Mac yedekleri: ~/Library/Application Support/BimmerTool/yedekler
''')
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert not any('simulator' in name or 'sim_' in name for name in archive.namelist())
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    print(package(parser.parse_args().output))
