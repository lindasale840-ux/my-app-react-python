import os
import tempfile
import subprocess

def find_ghostscript():
    candidates = [
        r"C:\Program Files\gs",
        r"C:\Program Files (x86)\gs"
    ]

    for base in candidates:
        if not os.path.exists(base):
            continue

        versions = sorted(
            os.listdir(base),
            reverse=True
        )

        for ver in versions:
            exe = os.path.join(
                base,
                ver,
                "bin",
                "gswin64c.exe"
            )

            if os.path.exists(exe):
                return exe

    return "gswin64c"


def run_pdf_version_downgrade(file_bytes: bytes, compatibility: str = "1.4"):
    # Tạo file tạm đầu vào
    temp_in = os.path.join(tempfile.gettempdir(), f"input_version_{os.urandom(4).hex()}.pdf")
    with open(temp_in, "wb") as f:
        f.write(file_bytes)

    # Đường dẫn file đầu ra
    temp_out = os.path.join(
        tempfile.gettempdir(),
        f"PDF_v{compatibility.replace('.', '_')}_{os.urandom(4).hex()}.pdf"
    )

    try:
        gs_exe = find_ghostscript()

        cmd = [
            gs_exe,
            "-sDEVICE=pdfwrite",
            f"-dCompatibilityLevel={compatibility}",
            "-dNOPAUSE",
            "-dBATCH",
            "-dQUIET",
            f"-sOutputFile={temp_out}",
            temp_in
        ]

        subprocess.run(
            cmd,
            check=True
        )

        return temp_out, None

    except Exception as e:
        return None, str(e)
    finally:
        # Dọn dẹp file tạm đầu vào
        if os.path.exists(temp_in):
            os.remove(temp_in)