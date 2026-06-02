"""Generate a one-page cover letter PDF from a .txt file.

Usage:
  python gen_cover_letter_pdf.py [input.txt] [output.pdf]
"""
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def build_pdf(text: str, out_path: Path) -> None:
    c = canvas.Canvas(str(out_path), pagesize=letter)
    width, height = letter
    left, top = 72, height - 72
    line_height = 14
    y = top
    max_width = width - 144

    for line in text.splitlines():
        if y < 72:
            c.showPage()
            y = top
        if not line.strip():
            y -= line_height * 0.6
            continue
        words = line.split(" ")
        chunk: list[str] = []
        for word in words:
            test = " ".join(chunk + [word])
            if c.stringWidth(test, "Helvetica", 11) <= max_width:
                chunk.append(word)
            else:
                if chunk:
                    c.setFont("Helvetica", 11)
                    c.drawString(left, y, " ".join(chunk))
                    y -= line_height
                chunk = [word]
        if chunk:
            c.setFont("Helvetica", 11)
            c.drawString(left, y, " ".join(chunk))
            y -= line_height

    c.save()


def main() -> None:
    default_txt = Path(__file__).parent.parent / "tracking/roles/Rain-Cover-Letter.txt"
    txt = Path(sys.argv[1]) if len(sys.argv) > 1 else default_txt
    out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else txt.parent / "Miles-Johnson-Rain-Cover-Letter.pdf"
    )
    build_pdf(txt.read_text(encoding="utf-8"), out)
    downloads = Path.home() / "Downloads" / "Miles Johnson - Rain Cover Letter.pdf"
    downloads.write_bytes(out.read_bytes())
    print(out)
    print(downloads)


if __name__ == "__main__":
    main()
