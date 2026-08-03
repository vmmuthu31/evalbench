"""
OCR evaluation metrics: CER, WER, Exact Match, Character Accuracy.
Uses jiwer for WER/CER; all metrics normalised to [0, 1] (lower = better for error rates).
"""

from __future__ import annotations
import unicodedata
import re


def _normalize(text: str) -> str:
    """Lowercase, strip, collapse whitespace, NFC normalise."""
    text = unicodedata.normalize("NFC", text.strip().lower())
    return re.sub(r"\s+", " ", text)


def cer(pred: str, ref: str) -> float:
    """Character Error Rate via edit distance."""
    pred = _normalize(pred)
    ref  = _normalize(ref)
    if not ref:
        return 0.0 if not pred else 1.0
    # Levenshtein at character level
    p_chars = list(pred)
    r_chars = list(ref)
    n, m = len(r_chars), len(p_chars)
    dp = list(range(n + 1))
    for j in range(1, m + 1):
        prev, dp[0] = dp[0], j
        for i in range(1, n + 1):
            temp = dp[i]
            if p_chars[j - 1] == r_chars[i - 1]:
                dp[i] = prev
            else:
                dp[i] = 1 + min(prev, dp[i], dp[i - 1])
            prev = temp
    return dp[n] / n


def wer(pred: str, ref: str) -> float:
    """Word Error Rate via edit distance on word tokens."""
    pred_toks = _normalize(pred).split()
    ref_toks  = _normalize(ref).split()
    if not ref_toks:
        return 0.0 if not pred_toks else 1.0
    n, m = len(ref_toks), len(pred_toks)
    dp = list(range(n + 1))
    for j in range(1, m + 1):
        prev, dp[0] = dp[0], j
        for i in range(1, n + 1):
            temp = dp[i]
            if pred_toks[j - 1] == ref_toks[i - 1]:
                dp[i] = prev
            else:
                dp[i] = 1 + min(prev, dp[i], dp[i - 1])
            prev = temp
    return dp[n] / n


def exact_match(pred: str, ref: str) -> float:
    """1.0 if normalized strings match exactly, else 0.0."""
    return 1.0 if _normalize(pred) == _normalize(ref) else 0.0


def char_accuracy(pred: str, ref: str) -> float:
    """Character accuracy = 1 - CER (clamped to [0, 1])."""
    return max(0.0, 1.0 - cer(pred, ref))


def compute_all(pred: str, ref: str) -> dict:
    c = cer(pred, ref)
    w = wer(pred, ref)
    return {
        "cer":           round(c, 4),
        "wer":           round(w, 4),
        "exact_match":   exact_match(pred, ref),
        "char_accuracy": round(1.0 - c, 4),
    }
