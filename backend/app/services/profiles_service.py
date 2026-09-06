"""
Content profiles.

A profile is the answer to "what kind of channel is this?" - and it is the only
place that answer lives. Before this, the niche was smeared across three files:
the feed list in config, the ranking weights in trends_service, and a script
prompt in generate_script.py that named the Bombay Stock Exchange out loud. A
gaming creator could not use the app without editing Python.

Now the niche is data. Six presets ship as YAML in `app/profiles/`; a creator
can also build their own in the dashboard, which is stored in B2 alongside their
credentials and behaves identically. Adding a seventh preset is a twenty-line
file, not a code change.

What a profile owns
-------------------
sources   which trend APIs are scanned, and with what arguments
persona   voice, audience, tone, hook style, call to action, and what to avoid
visuals   the style and subject vocabulary handed to the stock search
format    duration, YouTube category, hashtags
ranking   recency vs cross-source overlap, and the freshness cutoff
schedule  publish hours, timezone, videos per slot
"""
import copy
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from app.core.config import settings

logger = logging.getLogger(__name__)

PRESET_DIR = Path(__file__).resolve().parent.parent / "profiles"

# Custom profiles and the active choice live next to the credential vault, for
# the same reason: Render's disk does not survive a deploy.
_CUSTOM_KEY_SUFFIX = "config/profiles.json"
_STATE_KEY_SUFFIX = "config/profile_state.json"

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,40}$")

# Applied to every profile so a partial custom profile is still a valid one.
DEFAULTS: Dict[str, Any] = {
    "name": "Untitled",
    "tagline": "",
    "emoji": "\U0001F3AF",
    "accent": "#C9A227",
    "sources": [],
    "persona": {
        "voice": "a clear, engaging narrator",
        "audience": "a general audience",
        "tone": "conversational and concrete",
        "hook_style": "open on the most surprising fact",
        "cta": "Follow for more",
        "avoid": "",
    },
    "visuals": {
        "style": "clean editorial photography",
        "subjects": [],
        "prefer_clips": True,
    },
    "format": {
        "duration": 60,
        "youtube_category": "27",
        "hashtags": ["#shorts"],
    },
    "ranking": {"recency": 0.45, "trend": 0.55, "max_age_hours": 24.0},
    "schedule": {"hours": [9, 18], "timezone": "UTC", "top_n": 1},
}


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """One level of nesting is all a profile has, so this is deliberately shallow."""
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            merged = dict(result[key])
            merged.update({k: v for k, v in value.items() if v not in (None, "")})
            result[key] = merged
        elif value not in (None, "", [], {}):
            result[key] = value
    return _normalise(result)


def _as_list(value: Any) -> List[str]:
    """Accept a YAML list or a comma-separated string, always return a list.

    Both spellings are natural to write - `subjects: [a, b]` and
    `subjects: a, b` - and the second parses as a plain string. Joining that
    string later produced one entry per *character*, which reached the image
    prompt as "g, a, m, i, n, g". Coerce once here rather than defending
    against it at every read.
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(part).strip() for part in value if str(part).strip()]
    return [str(value).strip()]


def _normalise(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce the list-shaped fields so downstream code never has to check."""
    visuals = profile.get("visuals")
    if isinstance(visuals, dict):
        visuals["subjects"] = _as_list(visuals.get("subjects"))
    fmt = profile.get("format")
    if isinstance(fmt, dict):
        fmt["hashtags"] = _as_list(fmt.get("hashtags"))
    schedule = profile.get("schedule")
    if isinstance(schedule, dict):
        hours = []
        for hour in _as_list(schedule.get("hours")):
            try:
                value = int(float(hour))
            except (TypeError, ValueError):
                continue
            if 0 <= value <= 23:
                hours.append(value)
        schedule["hours"] = sorted(set(hours))
    return profile


class ProfileStore:
    def __init__(self) -> None:
        self._presets: Optional[Dict[str, Dict[str, Any]]] = None
        self._custom: Optional[Dict[str, Dict[str, Any]]] = None
        self._active: Optional[str] = None

    # -- presets ---------------------------------------------------------

    def _load_presets(self) -> Dict[str, Dict[str, Any]]:
        if self._presets is not None:
            return self._presets
        presets: Dict[str, Dict[str, Any]] = {}
        if PRESET_DIR.exists():
            for path in sorted(PRESET_DIR.glob("*.yaml")):
                try:
                    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                except Exception as exc:  # noqa: BLE001
                    # One malformed file must not take the whole picker down.
                    logger.warning("Skipping bad profile %s: %s", path.name, exc)
                    continue
                profile_id = (raw.get("id") or path.stem).strip()
                profile = _merge(DEFAULTS, raw)
                profile["id"] = profile_id
                profile["builtin"] = True
                presets[profile_id] = profile
        self._presets = presets
        logger.info("Loaded %d content profile(s): %s",
                    len(presets), ", ".join(sorted(presets)) or "none")
        return presets

    # -- custom ----------------------------------------------------------

    @property
    def _custom_key(self) -> str:
        return f"{settings.B2_PREFIX.strip('/')}/{_CUSTOM_KEY_SUFFIX}"

    @property
    def _state_key(self) -> str:
        return f"{settings.B2_PREFIX.strip('/')}/{_STATE_KEY_SUFFIX}"

    def _load_custom(self, refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        if self._custom is not None and not refresh:
            return self._custom
        from app.services.storage_service import storage

        data: Dict[str, Dict[str, Any]] = {}
        if storage.available:
            try:
                blob = storage.read_json(self._custom_key) or {}
                for profile_id, raw in (blob.get("profiles") or {}).items():
                    profile = _merge(DEFAULTS, raw)
                    profile["id"] = profile_id
                    profile["builtin"] = False
                    data[profile_id] = profile
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not read custom profiles: %s", exc)
        self._custom = data
        return data

    def _save_custom(self) -> None:
        from app.services.storage_service import storage

        if not storage.available:
            raise RuntimeError(
                "Custom profiles need Backblaze B2 - the local filesystem does "
                "not survive a redeploy."
            )
        payload = {
            profile_id: {k: v for k, v in profile.items() if k != "builtin"}
            for profile_id, profile in (self._custom or {}).items()
        }
        storage.put_json({"v": 1, "profiles": payload}, self._custom_key)

    # -- public ----------------------------------------------------------

    def all(self, refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        merged = dict(self._load_presets())
        merged.update(self._load_custom(refresh=refresh))
        return merged

    def list(self) -> List[Dict[str, Any]]:
        """Presets first, then custom - both alphabetical inside their group."""
        profiles = self.all()
        return sorted(
            profiles.values(),
            key=lambda p: (not p.get("builtin"), p.get("name", "").lower()),
        )

    def get(self, profile_id: str) -> Optional[Dict[str, Any]]:
        return self.all().get((profile_id or "").strip())

    def active_id(self, refresh: bool = False) -> str:
        """The chosen profile, falling back through state -> env -> first preset."""
        if self._active is not None and not refresh:
            return self._active

        from app.services.storage_service import storage

        chosen = ""
        if storage.available:
            try:
                state = storage.read_json(self._state_key) or {}
                chosen = (state.get("active") or "").strip()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not read the active profile: %s", exc)

        profiles = self.all()
        if chosen not in profiles:
            chosen = settings.CONTENT_PROFILE if settings.CONTENT_PROFILE in profiles else ""
        if not chosen and profiles:
            chosen = sorted(profiles)[0]
        self._active = chosen
        return chosen

    def active(self) -> Dict[str, Any]:
        """The active profile, or a usable default if there are somehow none.

        Never returns None. Everything downstream reads persona and format off
        this, and a null here would turn a missing YAML file into an exception
        in the middle of a render.
        """
        profile = self.get(self.active_id())
        if profile:
            return profile
        fallback = copy.deepcopy(DEFAULTS)
        fallback.update({"id": "default", "name": "Default", "builtin": True})
        return fallback

    def set_active(self, profile_id: str) -> Dict[str, Any]:
        from app.services.storage_service import storage

        profile = self.get(profile_id)
        if not profile:
            raise KeyError(f"No such content profile: {profile_id}")
        if storage.available:
            storage.put_json({"active": profile_id}, self._state_key)
        else:
            logger.warning(
                "B2 unavailable - the active profile will reset on restart."
            )
        self._active = profile_id
        # The sources changed, so anything cached against the old ones is stale.
        from app.services import trend_sources
        trend_sources.clear_cache()
        logger.info("Active content profile: %s", profile_id)
        return profile

    def save_custom(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        profile_id = (raw.get("id") or "").strip().lower().replace(" ", "_")
        if not _ID_RE.match(profile_id):
            raise ValueError(
                "Profile id must be 2-41 characters of lowercase letters, "
                "digits, hyphen or underscore."
            )
        if profile_id in self._load_presets():
            raise ValueError(
                f"'{profile_id}' is a built-in profile. Choose a different id."
            )
        self._load_custom(refresh=True)
        profile = _merge(DEFAULTS, raw)
        profile["id"] = profile_id
        profile["builtin"] = False
        self._custom[profile_id] = profile
        self._save_custom()
        logger.info("Saved custom content profile: %s", profile_id)
        return profile

    def delete_custom(self, profile_id: str) -> None:
        self._load_custom(refresh=True)
        if profile_id not in (self._custom or {}):
            raise KeyError(f"No such custom profile: {profile_id}")
        self._custom.pop(profile_id)
        self._save_custom()
        if self._active == profile_id:
            self._active = None  # recomputed on next read
        logger.info("Deleted custom content profile: %s", profile_id)


store = ProfileStore()


# ------------------------------------------------------------------ helpers --

def script_directives(profile: Optional[Dict[str, Any]] = None) -> str:
    """Turn a profile's persona into the block handed to the script model.

    This is the whole mechanism behind "choose your content type". The pipeline
    is identical for every niche; what changes is these eight lines of
    instruction and the stock-search vocabulary underneath them.
    """
    profile = profile or store.active()
    persona = profile.get("persona", {})
    visuals = profile.get("visuals", {})
    subjects = visuals.get("subjects") or []

    lines = [
        f"CHANNEL: {profile.get('name', 'Untitled')}"
        + (f" - {profile['tagline']}" if profile.get("tagline") else ""),
        f"NARRATOR: You are {persona.get('voice', 'a clear narrator')}.",
        f"AUDIENCE: {persona.get('audience', 'a general audience')}.",
        f"TONE: {persona.get('tone', 'conversational')}.",
        f"HOOK: {persona.get('hook_style', 'open on the most surprising fact')}.",
        f"CLOSE WITH: {persona.get('cta', 'Follow for more')}.",
        f"VISUAL STYLE: {visuals.get('style', 'clean editorial photography')}.",
    ]
    if subjects:
        lines.append(
            "PREFERRED VISUAL SUBJECTS (use these as the concrete, photographable "
            f"nouns in image prompts): {', '.join(subjects)}."
        )
    if persona.get("avoid"):
        # Last, and phrased as a hard constraint. Every profile carries one, and
        # for fitness and entertainment it is the difference between a publishable
        # video and one that should never have been made.
        lines.append(f"NEVER: {persona['avoid'].strip()}")
    return "\n".join(lines)


def ranking_weights(profile: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    profile = profile or store.active()
    ranking = profile.get("ranking", {})
    recency = float(ranking.get("recency", 0.45))
    trend = float(ranking.get("trend", 0.55))
    total = recency + trend
    # Normalise so a profile written as 60/40 and one written as 6/4 behave the
    # same, and a typo like 0.6/0.6 cannot push scores above 1.
    if total <= 0:
        recency, trend, total = 0.45, 0.55, 1.0
    return {
        "recency": recency / total,
        "trend": trend / total,
        "max_age_hours": float(ranking.get("max_age_hours", 24.0)),
    }
