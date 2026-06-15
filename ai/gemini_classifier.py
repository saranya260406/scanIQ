from google import genai
import json
import logging

logger = logging.getLogger('ai_processing')

class GeminiClassifier:

    def __init__(self, api_key):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        logger.info("Gemini Classifier initialized")

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