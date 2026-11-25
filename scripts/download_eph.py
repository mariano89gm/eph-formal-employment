"""
Descarga las bases de microdatos de la EPH (INDEC) y las descomprime.

Uso (desde la carpeta del proyecto):
    .venv\Scripts\python scripts\download_eph.py
"""
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

BASE_URL = "https://www.indec.gob.ar/ftp/cuadros/menusuperior/eph/"
YEARS = range(2017, 2027)          # 2017 a 2026
QUARTERS = [1, 2, 3, 4]
ORDINALS = {1: "1er", 2: "2do", 3: "3er", 4: "4to"}

RAW_DIR = Path("data/raw")
ZIP_DIR = RAW_DIR / "zips"


def candidate_names(year, q):
    """El INDEC no siempre usó el mismo formato de nombre: probamos variantes."""
    return [
        f"EPH_usu_{q}_Trim_{year}_txt.zip",
        f"EPH_usu_{ORDINALS[q]}_Trim_{year}_txt.zip",
        f"EPH_usu_{ORDINALS[q]}Trim_{year}_txt.zip",
    ]


def download(url, dest):
    """Descarga un archivo y devuelve True solo si es un zip válido."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())
    # Si el servidor devolvió una página de error en lugar del zip, la descartamos
    if not zipfile.is_zipfile(dest):
        dest.unlink()
        return False
    return True


def main():
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    missing = []

    for year in YEARS:
        for q in QUARTERS:
            out_dir = RAW_DIR / f"{year}_T{q}"
            if out_dir.exists():
                print(f"{year} T{q}: ya descargado, lo salteo")
                continue

            ok = False
            for name in candidate_names(year, q):
                zip_path = ZIP_DIR / name
                try:
                    ok = download(BASE_URL + name, zip_path)
                except urllib.error.HTTPError:
                    ok = False
                if ok:
                    with zipfile.ZipFile(zip_path) as zf:
                        zf.extractall(out_dir)
                    print(f"{year} T{q}: OK ({name})")
                    break
                time.sleep(0.5)

            if not ok:
                missing.append(f"{year} T{q}")
                print(f"{year} T{q}: no encontrado")
            time.sleep(1)  # pausa para no saturar el servidor del INDEC

    print("\nTrimestres no encontrados:", missing or "ninguno")


if __name__ == "__main__":
    main()