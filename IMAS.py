import os
import time
import json
import pandas as pd
from google import genai
from google.genai import types, errors
from PIL import Image

# ---------------- CONFIGURATION ----------------
API_KEY = "YOUR API KEY"

# Folder containing the screenshots
IMAGE_FOLDER_PATH = './ambassador_screenshots'

# I used 'gemini-flash-latest' because I confirmed I have access.
# It usually maps to 1.5 Flash, which has the best Free Tier limits.
MODEL_ID = 'gemini-flash-latest'

# Initialize Client
client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = """
You are a strict Compliance Auditor for the IMAS [Insert Full Name Here, e.g. International Martial Arts Society] Ambassador Program. 
Your task is to analyze screenshot evidence submitted by ambassadors to verify their work.

**STEP 1: IDENTITY EXTRACTION**
Search the image text for a username, social media handle, or profile name (e.g., "@john_doe", "Jane Smith", "LinkedIn User"). 
- If found, extract it exactly as written.
- If NO name is visible, output "Unknown_User".

**STEP 2: CONTENT ANALYSIS**
Scan the image for:
- **IMAS Branding:** Logos, specific keywords ("IMAS", "Ambassador", "Program"), or relevant hashtags.
- **Engagement:** Visible likes, comments, shares, or view counts.
- **Content Type:** Is it a public social media post, a webinar screenshot, or a private backend screen?

**STEP 3: SCORING RUBRIC (0-10)**
Assign a score based strictly on these criteria:

* **HIGH IMPACT (9-10 Points):** - Public social media post with *original* caption/commentary (not just a repost).
    - Visible engagement (likes/comments > 0) OR highly creative custom graphics.
    - Clear IMAS branding and advocacy.
* **MEDIUM IMPACT (6-8 Points):** - Standard repost/share of official IMAS content.
    - Screenshot of attending an IMAS webinar (must show the meeting interface).
    - Public post but with low/no visible engagement or minimal text.
* **LOW IMPACT (3-5 Points):** - "Backend" proof: Screenshots of login screens, reading an email, or private DMs.
    - Proof of simple tasks like "followed an account" or "liked a post".
* **INVALID (0-2 Points):** - Image is blurry, unreadable, or unrelated to IMAS.
    - Duplicate or corrupted image.

**OUTPUT FORMAT**
Return ONLY a valid JSON object. Do not include markdown formatting like ```json.
{
  "detected_name": "<extracted_name_or_Unknown>",
  "score": <integer_0_to_10>,
  "reasoning": "<concise_explanation_of_identity_and_score>"
}
"""


def analyze_with_retry(image_path):
    """
    Tries to analyze the image. If hit by a Rate Limit (429),
    it waits and retries automatically.
    """
    max_retries = 3
    base_wait = 10  # Start waiting 10 seconds if hit

    for attempt in range(max_retries):
        try:
            # Load Image
            img = Image.open(image_path)

            # API Call
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[SYSTEM_PROMPT, img],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )

            # Success! Parse JSON
            data = json.loads(response.text)
            return data.get('score', 0), data.get('reasoning', "No reasoning provided")

        except errors.ClientError as e:
            # Check if it is a 429 (Rate Limit) error
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = base_wait * (attempt + 1)  # Wait longer each time (10s, 20s, 30s)
                print(f"    [!] Rate Limit hit. Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                # If it's some other error (like 400 Bad Request), stop trying
                return 0, f"API Error: {str(e)}"
        except Exception as e:
            return 0, f"System Error: {str(e)}"

    return 0, "Failed after 3 retries (Rate Limit)"


def extract_id_from_filename(filename):
    # Safe extraction
    base = os.path.splitext(filename)[0]  # remove .png
    if "_" in base:
        return base.split('_')[0]
    return base


def main():
    print(f"Starting Grading using {MODEL_ID}...")

    # 1. Check Folder
    if not os.path.exists(IMAGE_FOLDER_PATH):
        print(f"Folder '{IMAGE_FOLDER_PATH}' not found.")
        return

    files = [f for f in os.listdir(IMAGE_FOLDER_PATH) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not files:
        print("No images found.")
        return

    results = []
    print(f"Found {len(files)} images.\n")

    # 2. Process Files
    for i, filename in enumerate(files):
        file_path = os.path.join(IMAGE_FOLDER_PATH, filename)
        ambassador_id = extract_id_from_filename(filename)

        print(f"[{i + 1}/{len(files)}] Analyzing {filename}...", end=" ", flush=True)

        # Call the robust function
        score, reason = analyze_with_retry(file_path)

        print(f"-> Score: {score}")

        results.append({
            'Ambassador_ID': ambassador_id,
            'Filename': filename,
            'Score': score,
            'Reasoning': reason
        })

        # Standard polite delay between calls (prevents hitting limit in the first place)
        time.sleep(2)

    # 3. Save Results
    if results:
        df = pd.DataFrame(results)

        # Create summary
        final_report = df.groupby('Ambassador_ID')['Score'].mean().reset_index()
        final_report.rename(columns={'Score': 'Average_Score'}, inplace=True)

        print("\n--- Grading Complete ---")
        print(final_report.head())

        df.to_csv('ai_graded_submissions_detailed.csv', index=False)
        final_report.to_csv('ambassador_final_grades.csv', index=False)
        print("\nResults saved to CSV files.")


if __name__ == "__main__":
    main()
