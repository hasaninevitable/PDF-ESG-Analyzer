"""
ESG PDF Extraction Utility - Fixed Version
Extracts sentences and headings with RAW PyMuPDF bounding boxes.
Let the frontend handle coordinate transformation.
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import nltk
from nltk.tokenize import sent_tokenize

# Ensure NLTK's sentence tokenizer data is present
nltk.download("punkt", quiet=True)

def is_heading(text, size):
    """Detect headings by format."""
    return text.isupper() and size > 16

def extract_pdf_regions(pdf_path):
    """Extract all headings and sentences with RAW PyMuPDF bounding boxes."""
    print(f"Loading PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    results = []
    print(f"Total pages found: {len(doc)}")

    for page_idx, page in enumerate(doc):
        page_w = page.rect.width
        page_h = page.rect.height
        blocks = page.get_text("dict").get("blocks", [])
        bulk = ""
        indices = []
        print(f"Processing Page {page_idx+1} (size: {page_w:.1f} x {page_h:.1f})...")

        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                sizes = [span["size"] for span in line["spans"] if span["text"].strip()]
                if not sizes:
                    continue
                fsize = max(sizes)
                line_txt = " ".join(span["text"].strip() for span in line["spans"] if span["text"].strip())
                if not line_txt:
                    continue

                if is_heading(line_txt, fsize):
                    bbox = line["bbox"]
                    print(f"  Found heading: '{line_txt[:30]}' at RAW {bbox}")
                    results.append({
                        "page": page_idx + 1,
                        "type": "heading",
                        "text": line_txt.strip(),
                        "coords": {
                            "x0": bbox[0],
                            "y0": bbox[1],  # Keep RAW PyMuPDF coordinates
                            "x1": bbox[2],
                            "y1": bbox[3]
                        },
                        "page_dimensions": {"width": page_w, "height": page_h},
                        "font_size": fsize
                    })
                else:
                    start_pos = len(bulk)
                    bulk += line_txt + " "
                    end_pos = len(bulk)
                    indices.append((start_pos, end_pos, line["bbox"]))

        print(f"  Assembled {len(indices)} spans on page {page_idx+1}.")

        # Tokenize to sentences and map bounding boxes
        for sent in sent_tokenize(bulk):
            sent_start = bulk.find(sent)
            if sent_start == -1: 
                continue
            sent_end = sent_start + len(sent)
            overlap_bboxes = [b for s, e, b in indices if not (e < sent_start or s > sent_end)]
            if not overlap_bboxes:
                print(f"    Skipped sentence (no bbox): '{sent[:32]}' ...")
                continue
                
            # Calculate combined bounding box
            x0 = min(b[0] for b in overlap_bboxes)
            y0 = min(b[1] for b in overlap_bboxes)
            x1 = max(b[2] for b in overlap_bboxes)
            y1 = max(b[3] for b in overlap_bboxes)
            
            print(f"    Sentence: '{sent[:32]}' at RAW ({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})")
            
            results.append({
                "page": page_idx + 1,
                "type": "sentence",
                "text": sent.strip(),
                "coords": {
                    "x0": x0,
                    "y0": y0,  # Keep RAW coordinates - no transformation
                    "x1": x1,
                    "y1": y1
                },
                "page_dimensions": {"width": page_w, "height": page_h}
            })

    doc.close()
    print(f"Extraction completed. Total regions: {len(results)}")
    return results

def ocr_fallback_regions(pdf_path):
    """Fallback OCR for image/scanned PDFs, returning RAW coordinates."""
    print(f"Starting OCR fallback for {pdf_path}")
    doc = fitz.open(pdf_path)
    gathered = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_w, page_h = page.rect.width, page.rect.height
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        print(f"OCR on page {page_idx + 1} (image size: {pix.width}x{pix.height})")
        
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        N = len(ocr_data['level'])
        print(f"  Detected {N} OCR regions.")
        
        for i in range(N):
            txt = ocr_data['text'][i].strip()
            if not txt:
                continue
                
            # Get OCR coordinates (top-left origin)
            x, y, w, h = (
                ocr_data['left'][i], 
                ocr_data['top'][i], 
                ocr_data['width'][i], 
                ocr_data['height'][i]
            )
            
            # Scale to PDF coordinate system
            sx = page_w / pix.width
            sy = page_h / pix.height
            
            # Convert OCR (top-left) to PyMuPDF (bottom-left) coordinates
            pdf_x0 = x * sx
            pdf_y0 = page_h - (y + h) * sy  # Convert to bottom-left origin
            pdf_x1 = (x + w) * sx
            pdf_y1 = page_h - y * sy
            
            print(f"    OCR word: '{txt[:15]}' at RAW ({pdf_x0:.1f}, {pdf_y0:.1f}, {pdf_x1:.1f}, {pdf_y1:.1f})")
            
            gathered.append({
                "page": page_idx + 1,
                "type": "sentence",
                "text": txt,
                "coords": {
                    "x0": pdf_x0,
                    "y0": pdf_y0,  # RAW PyMuPDF coordinates
                    "x1": pdf_x1,
                    "y1": pdf_y1
                },
                "page_dimensions": {"width": page_w, "height": page_h},
                "font_size": None
            })
    
    doc.close()
    print(f"OCR extraction finished. {len(gathered)} regions found.")
    return gathered

def extract_esg_pdf_sentences(pdf_path):
    """Main pipeline for extracting text with RAW coordinates for ESG analysis."""
    print("=== ESG PDF Extraction Pipeline ===")
    regions = extract_pdf_regions(pdf_path)
    
    if not regions:
        print("No text regions found, using OCR fallback...")
        regions = ocr_fallback_regions(pdf_path)
        if not regions:
            print("No regions found after OCR. Extraction failed.")
            return None
    
    print(f"Regions ready for downstream processing: {len(regions)} found.")
    print("📍 All coordinates are RAW PyMuPDF format - frontend will transform them.")
    return regions

# Legacy function for backward compatibility
def process_pdf_for_esg(pdf_path):
    """Wrapper function to match your existing app.py interface."""
    return extract_esg_pdf_sentences(pdf_path)