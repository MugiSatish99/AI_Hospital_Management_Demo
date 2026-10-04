import os
import shutil
import cv2
import numpy as np
import pytesseract
from PIL import Image
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Set tesseract path dynamically
tesseract_paths = [
    "tesseract",
    "/opt/homebrew/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract"
]

tesseract_cmd = None
for p in tesseract_paths:
    cmd = shutil.which(p)
    if cmd:
        tesseract_cmd = cmd
        break

if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def is_tesseract_available():
    if tesseract_cmd:
        return True
    return shutil.which("tesseract") is not None


def preprocess_image(pil_img, method="otsu"):
    # Convert PIL to CV2
    img = np.array(pil_img)
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
    # Resize to standard width (1200px) for better OCR accuracy
    height, width = img.shape
    new_width = 1200
    new_height = int((new_width / width) * height)
    img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    # Remove noise
    img = cv2.GaussianBlur(img, (3, 3), 0)
    
    # Thresholding
    if method == "otsu":
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == "adaptive":
        img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    elif method == "inv":
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
    return img


def extract_text_from_image(pil_img):
    if not isinstance(pil_img, Image.Image):
        raise ValueError("Unsupported image format. Please upload a valid JPG/PNG file.")
        
    if not is_tesseract_available():
        return "[Tesseract OCR binary not found. Please install via 'brew install tesseract' or consult administrator.]"

    # OCR Pipeline with automatic retry
    extracted_text = ""
    methods = ["otsu", "adaptive", "raw", "inv"]
    
    for method in methods:
        try:
            if method == "raw":
                img = np.array(pil_img)
                if len(img.shape) == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                processed = img
            else:
                processed = preprocess_image(pil_img, method)
                
            text = pytesseract.image_to_string(processed)
            if len(text.strip()) > len(extracted_text.strip()):
                extracted_text = text
                
            # If we got substantial text, we can stop
            if len(extracted_text.strip()) > 30:
                break
        except Exception as e:
            print(f"OCR Method {method} failed: {e}")
            
    return extracted_text.strip()


def analyze_ocr_report(ocr_text):
    if not ocr_text or "[Tesseract OCR" in ocr_text:
        return None
        
    import re
    
    prompt = f"""
You are an advanced medical assistant.
Analyze the following extracted medical report / prescription text:

---
{ocr_text}
---

Extract the following information:
1. Symptoms mentioned or implied.
2. Diagnosed conditions or issues.
3. Prescribed medicines.
4. Laboratory test values (e.g. glucose, HbA1c, BP) if present.

Return a concise summary of the symptoms and conditions to be fed into a disease prediction model.
"""
    try:
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        print("Error analyzing OCR report with Groq, running local extractor:", e)
        
        # Local regex fallback extraction
        text = str(ocr_text).lower()
        conditions = []
        condition_keywords = ["fever", "cough", "diabetes", "hypertension", "asthma", "bronchitis", "migraine", "arthritis", "gastritis", "flu", "allergy", "pneumonia", "stroke", "cardiac"]
        for kw in condition_keywords:
            if kw in text:
                conditions.append(kw.capitalize())
                
        meds = []
        med_keywords = ["metformin", "aspirin", "paracetamol", "acetaminophen", "amoxicillin", "atorvastatin", "lisinopril", "albuterol", "ibuprofen", "insulin", "amlodipine", "losartan"]
        for kw in med_keywords:
            if kw in text:
                meds.append(kw.capitalize())
                
        labs = []
        lab_keywords = ["hba1c", "blood sugar", "glucose", "blood pressure", "bp", "cholesterol", "hemoglobin", "thyroid", "tsh"]
        for kw in lab_keywords:
            if kw in text:
                match = re.search(rf"{kw}\s*[:=-]?\s*(\d+(\.\d+)?)", text)
                if match:
                    labs.append(f"{kw.upper()}: {match.group(1)}")
                else:
                    labs.append(kw.capitalize())
                    
        summary = []
        if conditions:
            summary.append(f"Implied Conditions: {', '.join(conditions)}")
        if meds:
            summary.append(f"Prescribed Medications: {', '.join(meds)}")
        if labs:
            summary.append(f"Lab values / Parameters: {', '.join(labs)}")
            
        if not summary:
            return f"Prescription content extracted: {ocr_text[:200]}..."
            
        return "Prescription Details (Local Extraction):\n" + "\n".join(summary)