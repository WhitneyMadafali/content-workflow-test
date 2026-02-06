#!/usr/bin/env python3
"""Extract professional terms from Excel work instruction files"""

from openpyxl import load_workbook
from pathlib import Path
import json
import re

# File paths
session_dir = Path(__file__).parent.parent / ".sharepoint-session"
files = [
    "WI-EN-001 E-3 Plus 整车装配-作业指导书 2024-12-13（中文）.xlsx",
    "WI-EN-004 S-6 整车装配-作业指导书 2025-11-30.xlsx",
    "WI-EN-005 PET3（7座）整车装配-作业指导书 2025-11-30.xlsx",
    "WI-EN-006 CET-3R_A 整车装配-作业指导书 2026-1-16.xlsx"
]

all_terms = set()
file_results = []

for filename in files:
    filepath = session_dir / filename
    print(f"\n📄 Processing: {filename}")
    
    if not filepath.exists():
        print(f"  ❌ File not found")
        continue
    
    file_size = filepath.stat().st_size / (1024 * 1024)
    print(f"  Size: {file_size:.2f} MB")
    
    try:
        wb = load_workbook(filepath, read_only=True, data_only=True)
        file_terms = set()
        
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            for row in sheet.iter_rows(values_only=True):
                for cell in row:
                    if cell and isinstance(cell, str):
                        text = str(cell).strip()
                        # 只提取包含中文的单词（不含空格、换行、标点分隔的短语）
                        if len(text) > 1 and re.search(r'[\u4e00-\u9fff]', text):
                            # 排除包含空格、换行符的长句
                            if ' ' not in text and '\n' not in text and len(text) <= 20:
                                file_terms.add(text)
                                all_terms.add(text)
        
        print(f"  ✓ Extracted {len(file_terms)} unique terms")
        file_results.append({
            "filename": filename,
            "terms_count": len(file_terms),
            "sample_terms": sorted(list(file_terms))[:50]
        })
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        continue

# Save results
output_file = Path(__file__).parent / "work-instructions-terms.json"
results = {
    "total_unique_terms": len(all_terms),
    "files": file_results,
    "all_terms_sample": sorted(list(all_terms))[:200]
}

output_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"\n✓ Results saved to: {output_file}")
print(f"✓ Total unique terms: {len(all_terms)}")
