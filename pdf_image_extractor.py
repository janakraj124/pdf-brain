# pdf_image_extractor.py
import os
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO


def extract_images_from_pdf(pdf_path, output_folder="extracted_images"):
    """
    PDF बाट सबै images निकाल्ने।
    Returns: list of image paths
    """
    os.makedirs(output_folder, exist_ok=True)
    
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    doc = fitz.open(pdf_path)
    
    image_paths = []
    
    for page_num, page in enumerate(doc, 1):
        images = page.get_images(full=True)
        
        for img_index, img in enumerate(images, 1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # Save गर्ने
            filename = f"{pdf_name}_p{page_num}_i{img_index}.{image_ext}"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            # सानो image skip (icon, logo)
            try:
                img_obj = Image.open(BytesIO(image_bytes))
                if img_obj.width < 100 or img_obj.height < 100:
                    os.remove(filepath)
                    continue
            except Exception:
                pass
            
            image_paths.append(filepath)
    
    doc.close()
    return image_paths


def extract_page_as_image(pdf_path, page_num=0, output_path="page.png"):
    """पूरा page लाई image बनाउने"""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    pix.save(output_path)
    doc.close()
    return output_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf = sys.argv[1]
        print(f"📄 PDF: {pdf}\n")
        images = extract_images_from_pdf(pdf)
        print(f"✅ {len(images)} images निकालियो:")
        for img in images:
            print(f"   • {img}")
    else:
        print("Usage: python pdf_image_extractor.py <pdf_path>")