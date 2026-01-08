# IMAS-Ambassador-Auto-Grader-
An AI-powered grading tool for community photo submissions, built with Python and Google Gemini.

📖 Backstory
During the IMAS 2025 Ambassador Program, the lead team I was part of manually reviewed thousands of screenshots to rank 100+ ambassadors for grants and sponsorships. This repository contains the automated solution I built retrospectively to solve that scaling problem.

⚙️ How it Works
Scans a folder of submission screenshots (Social media posts, webinar attendance, etc.).

Duplicate Check: Uses MD5 hashing to ensure no image is submitted twice.

AI Vision Analysis: Sends the image to Google Gemini 1.5 Flash with a strict grading rubric.

Scoring: The AI returns a score (0-10) and a reasoning (JSON format) explaining why it gave that score.

Reporting: Exports a CSV detailed report and a final leaderboard.

🧠 Reflection
Automation is powerful, but manual review builds community. This tool is designed to assist community managers, not replace the human connection entirely.

Current Limitations & Future Improvements:

Duplicate & Fraud Detection: Implementing "file hashing" to instantly catch if an Ambassador uploads the exact same screenshot twice to game the system (currently implemented in V2).

Cloud Native Integration: Removing the need to download files locally by connecting the script directly to the Google Drive API.

Metadata/EXIF Analysis: Checking the "date taken" on photos to ensure Ambassadors aren't submitting old work as new proof.

Human-in-the-Loop Flags: Instead of fully automating, the system should flag "borderline" scores (4-6/10) for human review, while auto-approving the obvious wins and auto-rejecting the bad data.

Multi-Language Support: Using translation capabilities to grade submissions in languages other than English without extra effort.
