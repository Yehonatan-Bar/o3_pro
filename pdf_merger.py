#!/usr/bin/env python3
"""
Simple PDF merger script that combines two or more PDF files into one.
"""

import sys
from pathlib import Path
try:
    from PyPDF2 import PdfMerger
except ImportError:
    print("PyPDF2 not found. Install with: pip install PyPDF2")
    sys.exit(1)


def merge_pdfs(input_files, output_file):
    """
    Merge multiple PDF files into a single PDF.

    Args:
        input_files (list): List of input PDF file paths
        output_file (str): Output PDF file path

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        merger = PdfMerger()

        for pdf_file in input_files:
            if not Path(pdf_file).exists():
                print(f"Error: File '{pdf_file}' not found")
                return False

            if not pdf_file.lower().endswith('.pdf'):
                print(f"Error: File '{pdf_file}' is not a PDF")
                return False

            print(f"Adding: {pdf_file}")
            merger.append(pdf_file)

        print(f"Saving merged PDF to: {output_file}")
        merger.write(output_file)
        merger.close()

        print("PDF merge completed successfully!")
        return True

    except Exception as e:
        print(f"Error merging PDFs: {str(e)}")
        return False


def main():
    """Command line interface for PDF merger"""
    if len(sys.argv) < 4:
        print("Usage: python pdf_merger.py <input1.pdf> <input2.pdf> [input3.pdf ...] <output.pdf>")
        print("Example: python pdf_merger.py file1.pdf file2.pdf file3.pdf merged.pdf")
        sys.exit(1)

    input_files = sys.argv[1:-1]  # All arguments except the last one
    output_file = sys.argv[-1]    # Last argument is output file

    print(f"Merging {len(input_files)} PDF files...")
    success = merge_pdfs(input_files, output_file)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()