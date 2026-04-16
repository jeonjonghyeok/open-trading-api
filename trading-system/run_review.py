"""
일일 복기 진입점 (08:00 KST 스케줄 — 출근 전 복기 확인용)
Usage:
  python run_review.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from analyzer import run_daily_review

if __name__ == "__main__":
    run_daily_review()
