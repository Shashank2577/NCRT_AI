import fitz  # PyMuPDF
import os
import json

# Dynamic Base Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PDF_DIR = os.path.join(BASE_DIR, "raw_pdfs")
OUTPUT_DIR = os.path.join(BASE_DIR, "parsed_output", "raw_text")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

def read_book_metadata(book_folder_path):
    metadata_file = os.path.join(book_folder_path, "book_metadata.txt")
    metadata = {}

    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            for line in f:
                if ':' in line:
                    key, value = line.strip().split(':', 1)
                    metadata[key.strip()] = value.strip()
    else:
        print(f"No metadata file found in {book_folder_path}. Using defaults.")

    return metadata

def extract_text_from_pdfs():
    extracted_pages = []
    page_counter = 1

    for class_folder in os.listdir(RAW_PDF_DIR):
        class_path = os.path.join(RAW_PDF_DIR, class_folder)
        if not os.path.isdir(class_path):
            continue

        for subject_folder in os.listdir(class_path):
            subject_path = os.path.join(class_path, subject_folder)
            if not os.path.isdir(subject_path):
                continue

            for book_folder in os.listdir(subject_path):
                book_path = os.path.join(subject_path, book_folder)
                if not os.path.isdir(book_path):
                    continue

                # Read book_metadata.txt
                metadata = read_book_metadata(book_path)
                metadata.setdefault("class", class_folder.replace("class_", ""))
                metadata.setdefault("subject", subject_folder)
                metadata.setdefault("book_name", book_folder)
                metadata.setdefault("book_version", "Unknown")
                metadata.setdefault("language", "English")
                metadata.setdefault("board", "NCERT")

                print(f"Processing book: {metadata['book_name']}")

                pdf_files = sorted([f for f in os.listdir(book_path) if f.endswith(".pdf")])

                for pdf_file in pdf_files:
                    pdf_path = os.path.join(book_path, pdf_file)
                    try:
                        doc = fitz.open(pdf_path)
                        print(f"  Processing {pdf_file}... Pages: {len(doc)}")

                        for page_num in range(len(doc)):
                            page = doc.load_page(page_num)
                            text = page.get_text("text").replace('\xa0', ' ').strip()

                            page_data = {
                                "global_page_number": page_counter,
                                "source_file": pdf_file,
                                "source_page_number": page_num + 1,
                                "text": text,
                                "class": metadata["class"],
                                "subject": metadata["subject"],
                                "book_name": metadata["book_name"],
                                "book_version": metadata["book_version"],
                                "language": metadata["language"],
                                "board": metadata["board"]
                            }

                            extracted_pages.append(page_data)
                            page_counter += 1

                    except Exception as e:
                        error_log = os.path.join(LOG_DIR, "text_extraction_errors.log")
                        with open(error_log, "a", encoding="utf-8") as f:
                            f.write(f"Error processing {pdf_file}: {str(e)}\n")
                        print(f"Error on {pdf_file}: {e}")

    # Save the merged extracted data
    output_path = os.path.join(OUTPUT_DIR, "merged_raw_text.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_pages, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Extraction completed successfully!")
    print(f"✅ Total pages processed: {len(extracted_pages)}")

if __name__ == "__main__":
    extract_text_from_pdfs()
