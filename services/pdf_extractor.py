import pymupdf

def extract_text_from_pdf(pdf_path):
    document = None
    try:
        document = pymupdf.open(pdf_path)
        pages = [page.get_text() for page in document]
        text = "\n".join(pages).strip()
        if not text:
            raise ValueError("No readable text found in this PDF.")
        return text
    except Exception as error:
        raise ValueError(f"PDF extraction failed: {error}")
    finally:
        if document:
            document.close()
