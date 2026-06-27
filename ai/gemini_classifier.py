from google import genai
import json
import logging
import re
import urllib.request

logger = logging.getLogger('ai_processing')


class GeminiClassifier:

    # ─────────────────────────────────────────────────────────────────
    # Rule-based system component patterns
    # AI-க்கு போறதுக்கு முன்னாடி இங்க filter ஆகும்
    # ─────────────────────────────────────────────────────────────────
    SYSTEM_COMPONENT_PATTERNS = [
        # Windows core / shell components
        r'^Microsoft\.Windows\..*',
        r'^MicrosoftWindows\..*',
        r'^windows\..*',
        r'^Windows\..*',

        # Runtimes / frameworks
        r'^Microsoft\.NET\.Native\..*',
        r'^Microsoft\.VCLibs\..*',
        r'^Microsoft\.UI\.Xaml\..*',
        r'^Microsoft\.WindowsAppRuntime.*',
        r'^Microsoft\.Services\.Store\..*',

        # System UI / shell components
        r'^Microsoft\.LockApp$',
        r'^Microsoft\.AAD\.BrokerPlugin$',
        r'^Microsoft\.BioEnrollment$',
        r'^Microsoft\.ECApp$',
        r'^Microsoft\.CredDialogHost$',
        r'^Microsoft\.AsyncTextService$',
        r'^Microsoft\.AccountsControl$',
        r'^Microsoft\.MicrosoftEdgeDevToolsClient$',
        r'^Microsoft\.Win32WebViewHost$',
        r'^Microsoft\.SecHealthUI$',
        r'^Microsoft\.WidgetsPlatformRuntime$',
        r'^Microsoft\.DesktopAppInstaller$',
        r'^Microsoft\.Edge\.GameAssist$',

        # Xbox system
        r'^Microsoft\.Xbox.*',
        r'^Microsoft\.XboxGameCallableUI$',
        r'^Microsoft\.XboxIdentityProvider$',

        # Mixed reality / Holo
        r'^Holo.*',
        r'^MixedReality.*',
        r'^Microsoft\.MixedReality\..*',
        r'^EnvironmentsApp$',
        r'^Passthrough$',
        r'^RoomAdjustment$',

        # Web auth bridges
        r'^WebAuthBridge.*',

        # Misc system
        r'^NcsiUwpApp$',
        r'^DesktopView$',
        r'^WhatsNew$',
        r'^aimgr$',
        r'^Microsoft\.Getstarted$',
        r'^microsoft\.windowscommunicationsapps$',

        # Pre-installed Microsoft Store bloatware
        r'^Microsoft\.Bing.*',
        r'^Microsoft\.People$',
        r'^Microsoft\.MicrosoftStickyNotes$',
        r'^Microsoft\.WindowsMaps$',
        r'^Microsoft\.ZuneVideo$',
        r'^Microsoft\.ZuneMusic$',
        r'^Microsoft\.WindowsSoundRecorder$',
        r'^Microsoft\.WindowsCamera$',
        r'^Microsoft\.WindowsCalculator$',
        r'^Microsoft\.WindowsNotepad$',
        r'^Microsoft\.WindowsTerminal$',
        r'^Microsoft\.Whiteboard$',
        r'^Microsoft\.Todos$',
        r'^Microsoft\.PowerAutomateDesktop$',
        r'^Microsoft\.RawImageExtension$',
        r'^Microsoft\.WebpImageExtension$',
        r'^Microsoft\.WebMediaExtensions$',
        r'^Microsoft\.HEIFImageExtension$',
        r'^Microsoft\.AV1VideoExtension$',
        r'^Clipchamp\.Clipchamp$',
        r'^MicrosoftCorporationII\..*',

        # OEM (HP / Intel) bloatware
        r'^AD2F1837\..*',
        r'^AppUp\.IntelGraphicsExperience$',

        # GUID-only package names
        r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',

        # Random-prefix store packages
        r'^[0-9A-Z]{5,}[A-Za-z]+\..*',
        r'^msstorefast\..*',
    ]

    def __init__(self, api_key):
        self.api_key = api_key
        self.client = None

        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                logger.info("Gemini Classifier initialized")
            except Exception as exc:
                logger.warning(
                    "Gemini client initialization failed; falling back to offline mode: %s",
                    exc,
                )
        else:
            logger.warning("No Gemini API key provided; running in offline mode")

        # Compile patterns once for performance
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.SYSTEM_COMPONENT_PATTERNS
        ]

    # ─────────────────────────────────────────────────────────────────
    # Helper: Rule-based system component detector
    # ─────────────────────────────────────────────────────────────────
    def _is_system_component_by_rule(self, app_name: str) -> bool:
        """Rule-based system component detection — FAST, NO API CALL."""
        if not app_name:
            return False

        for pattern in self._compiled_patterns:
            if pattern.match(app_name):
                return True
        return False

    # ─────────────────────────────────────────────────────────────────
    # Helper: Clean JSON response from Gemini
    # ─────────────────────────────────────────────────────────────────
    def _clean_json_response(self, response_text: str) -> str:
        """Gemini response-ல இருந்து markdown / code fences strip பண்ணும்."""
        text = response_text.strip()

        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\s*\n?', '', text)
            text = re.sub(r'\n?```\s*$', '', text)

        return text.strip()

    # ─────────────────────────────────────────────────────────────────
    # AI Deduplication
    # ─────────────────────────────────────────────────────────────────
    def deduplicate_apps(self, app_list: list) -> list:
        """
        DeduplicationEngine output-ஐ எடுத்து
        Gemini மூலம் similar app names identify பண்ணி
        clean unique list return பண்ணும்.
        """
        if not app_list:
            return []

        if not self.api_key or not self.client:
            logger.info("AI deduplication skipped because no Gemini API key is configured")
            return app_list

        logger.info(f"AI Deduplication started: {len(app_list)} apps")
        print(f"\n[AI Dedup] {len(app_list)} apps Gemini-க்கு அனுப்புகிறோம்...")

        # Index → name mapping
        name_index = {}
        for i, app in enumerate(app_list):
            name = app.get('name') or app.get('app_name') or 'Unknown'
            name_index[i] = name

        batch_size = 50
        indices = list(name_index.keys())
        batches = [
            indices[i:i + batch_size]
            for i in range(0, len(indices), batch_size)
        ]

        canonical_map = {}

        for b_num, batch_indices in enumerate(batches):
            logger.info(f"AI Dedup batch {b_num + 1}/{len(batches)}")
            try:
                batch_names = {str(i): name_index[i] for i in batch_indices}
                result_map = self._deduplicate_batch(batch_names)
                canonical_map.update(result_map)
            except Exception as e:
                logger.error(f"AI Dedup batch {b_num + 1} error: {e}")
                for i in batch_indices:
                    canonical_map[str(i)] = name_index[i]

        # Apply canonical names + merge duplicates
        seen_canonical = {}
        clean_list = []

        for i, app in enumerate(app_list):
            original_name = app.get('name') or app.get('app_name') or 'Unknown'
            canonical_name = canonical_map.get(str(i), original_name)

            if not canonical_name or not str(canonical_name).strip():
                canonical_name = original_name

            if canonical_name not in seen_canonical:
                app_copy = app.copy()
                app_copy['original_name'] = original_name
                app_copy['name'] = canonical_name

                if 'sources' not in app_copy:
                    app_copy['sources'] = [app.get('source', 'unknown')]

                seen_canonical[canonical_name] = len(clean_list)
                clean_list.append(app_copy)
            else:
                existing_idx = seen_canonical[canonical_name]
                existing = clean_list[existing_idx]

                new_sources = app.get('sources', [app.get('source', 'unknown')])
                existing_sources = existing.get('sources', [])

                for src in new_sources:
                    if src and src not in existing_sources:
                        existing_sources.append(src)

                existing['sources'] = existing_sources
                logger.debug(
                    f"AI Dedup merged: '{original_name}' → '{canonical_name}'"
                )

        logger.info(
            f"AI Dedup complete: {len(app_list)} → {len(clean_list)} apps"
        )
        print(
            f"[AI Dedup] Done: {len(app_list)} → {len(clean_list)} unique apps"
        )

        return clean_list

    def _deduplicate_batch(self, batch_names: dict) -> dict:
        """50 app names Gemini-க்கு அனுப்பி canonical mapping return பண்ணும்."""
        prompt = f"""
You are a Windows software expert. Below is a list of installed application names.

Your job:
1. Identify apps that are the same but have different names
   Example: "VLC", "VLC media player", "VideoLAN VLC" → all same app
2. For each app return the canonical (official/standard) name
3. If an app is unique, return its name as-is

Rules:
- Return ONLY valid JSON object, no explanation, no markdown, no code blocks
- Keep exact same index numbers (as strings) from input
- Canonical name = most recognized official name

Input:
{json.dumps(batch_names, indent=2)}

Return format:
{{
  "0": "canonical name",
  "1": "canonical name"
}}
"""
        response = self.client.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents=prompt
        )

        response_text = self._clean_json_response(response.text)

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Dedup JSON parse error: {e}")
            logger.error(f"Raw response: {response_text[:300]}")
            return {k: v for k, v in batch_names.items()}

        # Ensure all keys present
        for k, v in batch_names.items():
            if k not in result or not result[k]:
                result[k] = v

        return result

    # ─────────────────────────────────────────────────────────────────
    # Classification with 2-Layer Filtering
    # ─────────────────────────────────────────────────────────────────
    def classify_apps(self, app_list):
        """
        2-Layer Filtering:
        Layer 1: Rule-based filter (FAST, no API call)
        Layer 2: AI classification (only for remaining apps)
        Layer 3: AI-flagged system components removal
        """
        if not app_list:
            return []

        # ───── LAYER 1: Rule-based pre-filter ─────
        pre_filtered = []
        rule_filtered_count = 0

        for app in app_list:
            name = app.get('name') or app.get('app_name') or ''

            if self._is_system_component_by_rule(name):
                logger.info(f"[Rule Filter] System Component: {name}")
                rule_filtered_count += 1
                continue

            pre_filtered.append(app)

        logger.info(
            f"Rule-based Filter: {len(app_list)} → {len(pre_filtered)} "
            f"({rule_filtered_count} removed)"
        )
        print(
            f"[Rule Filter] {len(app_list)} → {len(pre_filtered)} "
            f"({rule_filtered_count} system components removed)"
        )

        if not pre_filtered:
            logger.info("No user apps remaining after rule filter")
            return []

        # ───── LAYER 2: AI classification ─────
        classified = []
        batch_size = 10
        batches = [
            pre_filtered[i:i + batch_size]
            for i in range(0, len(pre_filtered), batch_size)
        ]

        for i, batch in enumerate(batches):
            logger.info(f"AI Processing batch {i + 1}/{len(batches)}")

            try:
                result = self._classify_batch(batch)
                classified.extend(result)
            except Exception as e:
                logger.error(f"Batch {i + 1} classification error: {e}")

                for app in batch:
                    app['category'] = 'Unknown'
                    app['risk_level'] = 'Unknown'
                    app['is_necessary'] = 'Unknown'
                    app['recommendation'] = 'Unknown'
                    app['ai_description'] = ''
                    app['is_system_component'] = False

                classified.extend(batch)

        logger.info(f"AI Classification complete: {len(classified)} apps")

        # ───── LAYER 3: Remove AI-flagged system components ─────
        filtered_apps = []
        ai_filtered_count = 0

        for app in classified:
            if app.get('is_system_component', False):
                logger.info(
                    f"[AI Filter] System Component: "
                    f"{app.get('name', 'Unknown')}"
                )
                ai_filtered_count += 1
                continue
            filtered_apps.append(app)

        logger.info(
            f"Final Result: {len(app_list)} total → "
            f"{len(pre_filtered)} after rules → "
            f"{len(filtered_apps)} after AI "
            f"(rules removed {rule_filtered_count}, AI removed {ai_filtered_count})"
        )
        print(
            f"[Final] {len(app_list)} → {len(filtered_apps)} real user apps\n"
        )

        return filtered_apps

    def _classify_batch(self, batch):
        """10 apps-ஐ ஒரே call-ல classify பண்ணும்."""

        apps_data = []
        for app in batch:
            apps_data.append({
                'name': app.get('name', 'Unknown'),
                'publisher': app.get('publisher', 'Unknown'),
                'version': app.get('version', 'Unknown'),
                'type': app.get('type', 'Unknown')
            })

        prompt = f"""
You are an expert Windows Software Inventory Analyst.

Your goal is to identify ONLY genuine user-installed applications.

For each application return:
1. category
2. risk_level (Safe / Moderate / High)
3. is_necessary (Required / Optional / Unnecessary)
4. recommendation (Keep / Review / Remove)
5. description (short, 1 line)
6. is_system_component (true / false)

Set is_system_component = TRUE if application is:
- Windows built-in component (any Microsoft.Windows.*, MicrosoftWindows.*)
- Microsoft runtime / framework package (.NET.Native, VCLibs, UI.Xaml, WindowsAppRuntime)
- UWP system shell (LockApp, ShellExperienceHost, StartMenuExperienceHost)
- Pre-installed Microsoft Store app (BingNews, BingWeather, Calculator, Notepad,
  WindowsCamera, ZuneVideo, StickyNotes, Maps, Whiteboard, Todos, Clipchamp,
  PowerAutomateDesktop, Getstarted, communicationsapps)
- Image / Media codec extension (HEIF, WebP, AV1, RawImage, WebMedia)
- Xbox system component (Microsoft.Xbox*)
- Mixed Reality / Holo component
- OEM bloatware (HP, Intel, Dell pre-installed)
- GUID-only package name
- Driver / background system service
- Edge browser sub-component (Edge.GameAssist, EdgeDevToolsClient)

Set is_system_component = FALSE only if application is:
- Genuinely user-downloaded app (Chrome, Firefox, VS Code, Python, Git, Node.js)
- Third-party productivity software (Office, Adobe, Autodesk)
- Third-party media app (VLC, Spotify, OBS)
- Third-party security software (Norton, McAfee, Malwarebytes)
- Third-party utility (7-Zip, WinRAR, Notepad++)
- Developer tool (Docker, Postman, GitHub Desktop)

Examples:
Microsoft.Windows.ContentDeliveryManager → true
Microsoft.LockApp → true
Microsoft.WindowsCalculator → true
Microsoft.BingNews → true
Microsoft.WindowsTerminal → true
Clipchamp.Clipchamp → true
AD2F1837.HPSupportAssistant → true
Microsoft.UI.Xaml.2.7 → true
Microsoft.VCLibs.140.00 → true

Visual Studio Code → false
PythonSoftwareFoundation.Python.3.12 → false
Google Chrome → false
GitHub Desktop → false
VLC media player → false
7-Zip → false

Apps to analyze:
{json.dumps(apps_data, indent=2)}

Return ONLY a valid JSON array, no markdown, no code fences.

Example:
[
  {{
    "name": "Visual Studio Code",
    "category": "Development",
    "risk_level": "Safe",
    "is_necessary": "Optional",
    "recommendation": "Keep",
    "description": "Source code editor",
    "is_system_component": false
  }}
]
"""
        response = self.client.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents=prompt
        )

        response_text = self._clean_json_response(response.text)

        print("\n===== GEMINI RESPONSE =====")
        print(response_text[:500])
        print("===========================\n")

        try:
            ai_results = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Classify JSON parse error: {e}")
            logger.error(f"Raw response: {response_text[:300]}")
            ai_results = []

        # Merge AI results with original data
        enriched = []
        for j, app in enumerate(batch):
            try:
                if j < len(ai_results):
                    ai_data = ai_results[j]
                    app['category'] = ai_data.get('category', 'Unknown')
                    app['risk_level'] = ai_data.get('risk_level', 'Unknown')
                    app['is_necessary'] = ai_data.get('is_necessary', 'Unknown')
                    app['recommendation'] = ai_data.get('recommendation', 'Unknown')
                    app['ai_description'] = ai_data.get('description', '')
                    app['is_system_component'] = ai_data.get(
                        'is_system_component', False
                    )
                else:
                    raise IndexError("AI result missing for this app")
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

    # ─────────────────────────────────────────────────────────────────
    # Utility: Internet check
    # ─────────────────────────────────────────────────────────────────
    def check_internet(self):
        """Internet connection check பண்ணும்."""
        try:
            urllib.request.urlopen('https://www.google.com', timeout=5)
            return True
        except Exception:
            return False
