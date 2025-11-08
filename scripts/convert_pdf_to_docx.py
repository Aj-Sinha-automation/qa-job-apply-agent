#!/usr/bin/env python3
"""
Convert data/Resume-ANURAJ.pdf -> data/base_resume.docx
Requires: pdf2docx
"""
import os
from pdf2docx import Converter

PDF_IN = "data/Resume-ANURAJ.pdf"
DOCX_OUT = "data/base_resume.docx"

def convert():
    if not os.path.exists(PDF_IN):
        raise FileNotFoundError(f"Input PDF not found: {PDF_IN}")
    os.makedirs(os.path.dirname(DOCX_OUT), exist_ok=True)
    cv = Converter(PDF_IN)
    cv.convert(DOCX_OUT, start=0, end=None)
    cv.close()
    print(f"Converted {PDF_IN} -> {DOCX_OUT}")

if __name__ == "__main__":
    convert()
