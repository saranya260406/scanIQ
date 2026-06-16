from google import genai
import json
import logging

logger = logging.getLogger('ai_processing')

class GeminiClassifier:

    def __init__(self, api_key):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        logger.info("Gemini Classifier initialized")

    # ─────────────────────────────────────────────────────────────────
    # NEW: AI Deduplication Method
    # core/deduplication_engine.py output-ஐ இங்க அனுப்பு
    # Gemini similar/near-duplicate names identify பண்ணி
    # canonical name கொடுக்கும்
    # ─────────────────────────────────────────────────────────────────
    def deduplicate_apps(self, app_list: list) -> list:
        """
        DeduplicationEngine.deduplicate() output-ஐ எடுத்து
        Gemini மூலம் similar app names identify பண்ணி
        clean unique list return பண்ணும்.

        Args:
            app_list (list): core/deduplication_engine.py output

        Returns:
            list: AI-filtered unique app list with canonical names
        """
        if not app_list:
            return []

        logger.info(f"AI Deduplication started: {len(app_list)} apps")
        print(f"\n[AI Dedup] {len(app_list)} apps Gemini-க்கு அனுப்புகிறோம்...")

        # Index → name mapping உருவாக்கு
        name_index = {}
        for i, app in enumerate(app_list):
            name = app.get('name') or app.get('app_name') or 'Unknown'
            name_index[i] = name

        # 50 names per batch
        batch_size = 50
        indices = list(name_index.keys())
        batches = [indices[i:i+batch_size] for i in range(0, len(indices), batch_size)]

        # canonical map: index → canonical_name
        canonical_map = {}

        for b_num, batch_indices in enumerate(batches):
            logger.info(f"AI Dedup batch {b_num+1}/{len(batches)}")
            try:
                batch_names = {str(i): name_index[i] for i in batch_indices}
                result_map = self._deduplicate_batch(batch_names)
                canonical_map.update(result_map)
            except Exception as e:
                logger.error(f"AI Dedup batch {b_num+1} error: {e}")
                # Error வந்தா original name-ஐ வச்சுக்கோ
                for i in batch_indices:
                    canonical_map[str(i)] = name_index[i]

        # Canonical name apply பண்ணி duplicates remove பண்ணு
        seen_canonical = {}
        clean_list = []

        for i, app in enumerate(app_list):
            canonical_name = canonical_map.get(str(i), app.get('name') or app.get('app_name') or 'Unknown')

            if canonical_name not in seen_canonical:
                # புதுசு — add பண்ணு
                app_copy = app.copy()
                app_copy['original_name'] = app.get('name') or app.get('app_name') or 'Unknown'
                app_copy['name'] = canonical_name
                seen_canonical[canonical_name] = len(clean_list)
                clean_list.append(app_copy)
            else:
                # Duplicate — sources மட்டும் merge பண்ணு
                existing_idx = seen_canonical[canonical_name]
                existing = clean_list[existing_idx]
                new_sources = app.get('sources', [app.get('source', 'unknown')])
                existing_sources = existing.get('sources', [])
                for src in new_sources:
                    if src not in existing_sources:
                        existing_sources.append(src)
                existing['sources'] = existing_sources
                logger.debug(f"AI Dedup merged: '{app.get('name')}' → '{canonical_name}'")

        logger.info(f"AI Dedup complete: {len(app_list)} → {len(clean_list)} apps")
        print(f"[AI Dedup] Done: {len(app_list)} → {len(clean_list)} unique apps")

        return clean_list

    def _deduplicate_batch(self, batch_names: dict) -> dict:
        """
        50 app names Gemini-க்கு அனுப்பி
        canonical name mapping return பண்ணும்.

        Args:
            batch_names (dict): {"0": "VLC", "1": "VLC media player", ...}

        Returns:
            dict: {"0": "VLC media player", "1": "VLC media player", ...}
        """
        prompt = f"""
You are a Windows software expert. Below is a list of installed application names.

Your job:
1. Identify apps that are the same but have different names
   Example: "VLC", "VLC media player", "VideoLAN VLC" → all same app
2. For each app return the canonical (official/standard) name
3. If an app is unique, return its name as-is

Rules:
- Return ONLY valid JSON object, no explanation, no markdown, no code blocks
- Keep exact same index numbers from input
- Canonical name = most recognized official name

Input:
{json.dumps(batch_names, indent=2)}

Return format:
{{
  "0": "canonical name",
  "1": "canonical name",
  ...
}}
"""
        response = self.client.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents=prompt
        )

        response_text = response.text.strip()

        # Markdown strip பண்ணு
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])

        return json.loads(response_text)

    # ─────────────────────────────────────────────────────────────────
    # EXISTING: Classification Method (மாத்தல் இல்லை)
    # ─────────────────────────────────────────────────────────────────
    def classify_apps(self, app_list):
        """
        App list-ஐ batch-ஆ Gemini-க்கு அனுப்பி
        classify பண்ணும்
        """
        classified = []
        # 10 apps per batch
        batch_size = 10
        batches = [app_list[i:i+batch_size] for i in range(0, len(app_list), batch_size)]

        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)}")
            try:
                result = self._classify_batch(batch)
                classified.extend(result)
            except Exception as e:
                logger.error(f"Batch {i+1} classification error: {e}")
                # Error வந்தா original data return பண்ணும்
                classified.extend(batch)

        logger.info(f"Classification complete: {len(classified)} apps")
        return classified

    def _classify_batch(self, batch):
        """10 apps-ஐ ஒரே call-ல classify பண்ணும்"""

        # Gemini-க்கு அனுப்பற data prepare பண்ணும்
        apps_data = []
        for app in batch:
            apps_data.append({
                'name': app.get('name', 'Unknown'),
                'publisher': app.get('publisher', 'Unknown'),
                'version': app.get('version', 'Unknown'),
                'type': app.get('type', 'Unknown')
            })

        prompt = f"""
You are a Windows software analyst. Analyze these applications and classify each one.

For each app provide:
1. category: (Development/Security/Media/Office/Gaming/Browser/Utility/Bloatware/Malware/Unknown)
2. risk_level: (Safe/Low Risk/Suspicious/Dangerous)
3. is_necessary: (Yes/No/Optional)
4. recommendation: (Keep/Can Remove/Should Remove/Remove Immediately)
5. description: (one line - what this app does)
6. is_system_component: (true/false - is it a Windows system component?)

Apps to analyze:
{json.dumps(apps_data, indent=2)}

Return ONLY a valid JSON array with same order as input.
No extra text, no markdown, no code blocks.
Example format:
[
  {{
    "name": "App Name",
    "category": "Development",
    "risk_level": "Safe",
    "is_necessary": "Optional",
    "recommendation": "Keep",
    "description": "Code editor",
    "is_system_component": false
  }}
]
"""
        response = self.client.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents=prompt
        )

        response_text = response.text.strip()

        # JSON parse பண்ணும்
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]

        ai_results = json.loads(response_text)

        # Original data + AI results merge பண்ணும்
        enriched = []
        for j, app in enumerate(batch):
            try:
                ai_data = ai_results[j]
                app['category'] = ai_data.get('category', 'Unknown')
                app['risk_level'] = ai_data.get('risk_level', 'Unknown')
                app['is_necessary'] = ai_data.get('is_necessary', 'Unknown')
                app['recommendation'] = ai_data.get('recommendation', 'Unknown')
                app['ai_description'] = ai_data.get('description', '')
                app['is_system_component'] = ai_data.get('is_system_component', False)
            except Exception as e:
                logger.error(f"App merge error: {e}")
                app['category'] = 'Unknown'
                app['risk_level'] = 'Unknown'
                app['is_necessary'] = 'Unknown'
                app['recommendation'] = 'Unknown'
                app['ai_description'] = ''
                app['is_system_component'] = False
            enriched.append(app)

        return enriched

    def check_internet(self):
        """Internet connection check பண்ணும்"""
        import urllib.request
        try:
            urllib.request.urlopen('https://www.google.com', timeout=5)
            return True
        except Exception:
            return False