from pathlib import Path


def load_document_text(path: Path, content_type: str | None = None) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf" or content_type == "application/pdf":
        return _load_pdf(path)
    if suffix == ".docx" or content_type in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }:
        return _load_docx(path)
    if suffix in {".md", ".markdown", ".txt", ".csv", ".html", ".htm"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _load_docx(path: Path) -> str:
    from docx import Document

    document = Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)
