
from pathlib import Path
from pypdf import PdfReader

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Input and output directories
CORPUS_DIR = BASE_DIR / "corpus"
OUTPUT_DIR = BASE_DIR / "docs" / "planning" / "extracted_text"

# Create output folder if it does not exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Find all PDF files
pdf_files = list(CORPUS_DIR.rglob("*.pdf"))

if not pdf_files:
    print("ERROR: No PDF files found.")
    raise SystemExit(1)

print("=" * 55)
print("PHARMASAFE AI - CORPUS TEXT EXTRACTION")
print("=" * 55)

for pdf_path in pdf_files:

    print(f"\nProcessing: {pdf_path.name}")

    try:
        reader = PdfReader(str(pdf_path))

        pages = []

        for page_number, page in enumerate(reader.pages, start=1):

            content = page.extract_text() or ""

            pages.append(
                f"\n--- PAGE {page_number} ---\n{content}"
            )

        full_text = "\n".join(pages)

        output_file = OUTPUT_DIR / f"{pdf_path.stem}.txt"

        output_file.write_text(
            full_text,
            encoding="utf-8"
        )

        print(f"Total pages: {len(reader.pages)}")
        print(f"Extracted characters: {len(full_text)}")
        print(f"Saved file: {output_file}")

        if len(full_text.strip()) < 500:
            print("WARNING: Very little text extracted.")
            print("OCR may be required.")
        else:
            print("STATUS: Extraction successful.")

    except Exception as error:

        print(f"ERROR: {error}")

print("\n" + "=" * 55)
print("CORPUS EXTRACTION COMPLETED")
print("=" * 55)
