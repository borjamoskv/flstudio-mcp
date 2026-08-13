#!/usr/bin/env python3
"""
C5-REAL ENTROPY & EPISTEMIC REDUNDANCY AUDITOR
===============================================
Audits document entropy, Jaccard token similarity, header duplication,
and workspace structural fragmentation.
"""

import os
import re
from collections import defaultdict

WORKSPACE = os.path.expanduser("~/10_PROJECTS/flstudio-mcp")

def get_markdown_files(root_dir):
    md_files = []
    for root, dirs, files in os.walk(root_dir):
        if "node_modules" in root or ".venv" in root or ".git" in root:
            continue
        for f in files:
            if f.endswith((".md", ".txt", ".json", ".py")):
                md_files.append(os.path.join(root, f))
    return md_files

def tokenize(text):
    words = re.findall(r'\w+', text.lower())
    return set(words)

def jaccard_similarity(set1, set2):
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union

def audit_entropy():
    print("=== [C5-REAL EPISTEMIC ENTROPY AUDIT INITIALIZATION] ===")
    files = get_markdown_files(WORKSPACE)
    print(f"Scanned files count: {len(files)}")
    
    file_tokens = {}
    file_headers = defaultdict(list)
    
    for fpath in files:
        rel_path = os.path.relpath(fpath, WORKSPACE)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                file_tokens[rel_path] = tokenize(content)
                
                # Extract markdown headers
                headers = re.findall(r'^(#{1,6}\s+.+)$', content, re.MULTILINE)
                for h in headers:
                    file_headers[h.strip()].append(rel_path)
        except Exception as e:
            pass

    # 1. Jaccard Similarity Audit
    duplicates = []
    file_list = list(file_tokens.keys())
    for i in range(len(file_list)):
        for j in range(i + 1, len(file_list)):
            f1, f2 = file_list[i], file_list[j]
            sim = jaccard_similarity(file_tokens[f1], file_tokens[f2])
            if sim > 0.75 and f1 != f2:
                duplicates.append((f1, f2, sim))
                
    print("\n■ 1. HIGH-FRICTION CLONES (Jaccard > 0.75):")
    if duplicates:
        for f1, f2, sim in duplicates:
            print(f"  ⚠️ [{sim*100:.1f}% Similarity] {f1} <---> {f2}")
    else:
        print("  ✅ Zero structural clones detected (Jaccard < 0.75 across all files)")

    # 2. Header Duplication Audit
    print("\n■ 2. INTRA-CORPUS HEADER REPETITION:")
    repeated_headers = {h: paths for h, paths in file_headers.items() if len(paths) > 1}
    if repeated_headers:
        for h, paths in list(repeated_headers.items())[:10]:
            print(f"  ⚠️ Header '{h}' repeated in {len(paths)} files: {', '.join(paths[:3])}")
    else:
        print("  ✅ Zero header collisions detected")

    # 3. Overall Entropy Calculation
    total_files = len(files)
    clone_count = len(duplicates)
    entropy_score = (clone_count / (total_files if total_files > 0 else 1)) * 100.0
    
    print("\n" + "="*60)
    print(f"THERMODYNAMIC ENTROPY SCORE: {entropy_score:.2f}% (Target: < 5.0%)")
    print(f"STATUS: {'HIGH EXERGY / CLEAN' if entropy_score < 5.0 else 'ANERGY DETECTED'}")
    print("="*60)

if __name__ == "__main__":
    audit_entropy()
