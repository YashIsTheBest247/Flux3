"""
Credential vault.

Holds the one credential that is genuinely per-visitor: the OAuth client of a
creator who wants finished videos on their own YouTube channel rather than the
one this deployment publishes to by default.

Everything else - the model key, the stock-photo keys, Backblaze - comes from
the environment and is set once at deploy time. Those are the operator's cost
centre and are identical for every visitor, so a public form asking for them
was both pointless and an invitation to paste a key that then billed someone.

Where the secrets live
----------------------
Encrypted with Fernet and written to Backblaze B2 at
``{B2_PREFIX}/config/credentials.enc``. B2 rather than disk because Render's
filesystem is ephemeral: anything written locally is gone on the next deploy,
and a creator who has to reconnect their channel after every push will stop
using the tool.

Where the encryption key comes from
-----------------------------------
``FLUX_SECRET_KEY`` if set. If it is not, the key is derived from the B2
application key instead - already a secret, already required for the app to
store anything at all, and already stable across deploys. That makes the vault
work out of the box rather than adding another thing to configure before
anything runs. It is a real tradeoff, logged loudly: anyone holding the B2 key
can decrypt the vault. Set FLUX_SECRET_KEY to separate the two.
"""
import base64
import json
import logging
import os
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)

# Fixed salt. A random per-install salt would have to be stored next to the
# ciphertext to be usable, which buys nothing here - the secret is the key
# material, not the salt, and the threat model is "someone read the bucket",
# not "someone is running a rainbow table against one blob".
_SALT = b"flux-credential-vault-v1"
_ITERATIONS = 240_000


class CredentialField:
    """One credential the dashboard can set."""

    def __init__(
        self,
        key: str,
        label: str,
        group: str,
        help_text: str = "",
        secret: bool = True,
        required: bool = False,
        placeholder: str = "",
        docs_url: str = "",
    ) -> None:
        self.key = key
        self.label = label
        self.group = group
        self.help_text = help_text
        self.secret = secret
        self.required = required
        self.placeholder = placeholder
        self.docs_url = docs_url


# What the dashboard can set - and deliberately nothing else.
#
# Model and stock-library keys used to be here. They are not any more: they are
# the deployment's own cost centre, they are the same for every visitor, and
# putting them in a public form invited someone to paste a key that then billed
# them. Those now come from the environment and are set once, at deploy time.
#
# What is left is the only credential that is genuinely per-visitor: the OAuth
# client for a creator who wants uploads on their own channel instead of the
# default one.
FIELDS: List[CredentialField] = [
    CredentialField(
        "YOUTUBE_CLIENT_ID", "OAuth client ID", "Your channel",
        help_text="From your own Google Cloud project, with the YouTube Data "
                  "API v3 enabled.",
        secret=False, placeholder="....apps.googleusercontent.com",
        docs_url="https://console.cloud.google.com/apis/credentials",
    ),
    CredentialField(
        "YOUTUBE_CLIENT_SECRET", "OAuth client secret", "Your channel",
        help_text="Paired with the client ID. Encrypted before it is stored, "
                  "and never returned to the browser once saved.",
        placeholder="GOCSPX-...",
    ),
]

# Where finished videos go.
#   "default" - the channel this deployment owns, from YOUTUBE_TOKEN_JSON in the
#               environment. Nothing to configure; a visitor can publish
#               immediately.
#   "own"     - the visitor's own channel, connected through OAuth below.
PUBLISH_DEFAULT = "default"
PUBLISH_OWN = "own"

_FIELD_KEYS = {f.key for f in FIELDS}
# Written by the OAuth callback rather than typed into a form, but stored in the
# same vault and cleared by the same "disconnect" path.
_INTERNAL_KEYS = {"YOUTUBE_TOKEN_JSON", "YOUTUBE_CHANNEL_TITLE", "YOUTUBE_CHANNEL_ID",
                  "PUBLISH_MODE"}
ALL_KEYS = _FIELD_KEYS | _INTERNAL_KEYS


class CredentialVault:
    def __init__(self) -> None:
        self._cache: Optional[Dict[str, str]] = None
        self._fernet: Optional[Fernet] = None
        self._load_error: Optional[str] = None

    # -- key material ----------------------------------------------------

    def _key_material(self) -> Optional[str]:
        explicit = (settings.FLUX_SECRET_KEY or "").strip()
        if explicit:
            return explicit
        fallback = (settings.B2_APP_KEY or "").strip()
        if fallback:
            return fallback
        return None

    def _cipher(self) -> Optional[Fernet]:
        if self._fernet is not None:
            return self._fernet
        material = self._key_material()
        if not material:
            return None
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=_SALT, iterations=_ITERATIONS
        )
        self._fernet = Fernet(base64.urlsafe_b64encode(kdf.derive(material.encode())))
        return self._fernet

    # -- persistence -----------------------------------------------------

    @property
    def _object_key(self) -> str:
        return f"{settings.B2_PREFIX.strip('/')}/config/credentials.enc"

    def _read(self) -> Dict[str, str]:
        """Decrypt the stored vault.

        Any failure yields an empty vault and a logged reason. A creator with an
        unreadable vault should see an empty settings form they can fill in
        again, not a 500 on every page load.
        """
        from app.services.storage_service import storage

        cipher = self._cipher()
        if cipher is None:
            self._load_error = (
                "No encryption key available. Set FLUX_SECRET_KEY, or configure "
                "Backblaze B2 - its app key is used as the fallback."
            )
            return {}
        if not storage.available:
            self._load_error = "Backblaze B2 is not configured, so the vault cannot be stored."
            return {}

        try:
            blob = storage.read_json(self._object_key)
        except Exception as exc:  # noqa: BLE001
            self._load_error = f"Could not read the vault from B2: {exc}"
            logger.warning(self._load_error)
            return {}

        if not blob:
            self._load_error = None
            return {}

        try:
            raw = cipher.decrypt(blob["payload"].encode())
        except (InvalidToken, KeyError, AttributeError):
            # Almost always the encryption key changed - FLUX_SECRET_KEY was set
            # after the fact, or the B2 key was rotated. Say so, because
            # "my credentials disappeared" is otherwise baffling.
            self._load_error = (
                "The stored credentials could not be decrypted - the encryption "
                "key has changed since they were saved. Re-enter them to "
                "overwrite the old vault."
            )
            logger.warning(self._load_error)
            return {}

        try:
            data = json.loads(raw.decode())
        except Exception as exc:  # noqa: BLE001
            self._load_error = f"Vault contents are not valid JSON: {exc}"
            return {}

        self._load_error = None
        return {k: v for k, v in data.items() if k in ALL_KEYS and isinstance(v, str)}

    def _write(self, data: Dict[str, str]) -> None:
        from app.services.storage_service import storage

        cipher = self._cipher()
        if cipher is None:
            raise RuntimeError(
                "Cannot save credentials: no encryption key. Set FLUX_SECRET_KEY."
            )
        if not storage.available:
            raise RuntimeError(
                "Cannot save credentials: Backblaze B2 is not configured, and "
                "the local filesystem does not survive a redeploy."
            )
        token = cipher.encrypt(json.dumps(data).encode()).decode()
        storage.put_json({"v": 1, "payload": token}, self._object_key)

    # -- public API ------------------------------------------------------

    def all(self, refresh: bool = False) -> Dict[str, str]:
        if self._cache is None or refresh:
            self._cache = self._read()
        return dict(self._cache)

    def get(self, key: str, default: str = "") -> str:
        return self.all().get(key) or default

    def save(self, updates: Dict[str, Any]) -> Dict[str, str]:
        """Merge updates in, persist, and push the result into live settings.

        An empty string means *clear this field*; a key that is absent is left
        alone. That distinction is what lets the dashboard submit only the
        fields the creator actually touched - a form that round-tripped its
        masked values would otherwise write the mask over the real secret.
        """
        data = self.all(refresh=True)
        for key, value in updates.items():
            if key not in ALL_KEYS:
                continue
            text = "" if value is None else str(value).strip()
            if text:
                data[key] = text
            else:
                data.pop(key, None)
        self._write(data)
        self._cache = data
        self.apply_to_settings()
        return data

    def clear(self, keys: List[str]) -> None:
        data = self.all(refresh=True)
        for key in keys:
            data.pop(key, None)
            os.environ.pop(key, None)
            if hasattr(settings, key):
                try:
                    setattr(settings, key, "")
                except Exception:  # noqa: BLE001
                    pass
        self._write(data)
        self._cache = data
        self.apply_to_settings()

    def apply_to_settings(self) -> None:
        """Overlay the vault onto the live Settings object.

        Both `settings` and `os.environ` are updated: most code reads the
        settings object, but a few third-party clients read the environment
        directly, and a credential that works in one place and not the other is
        a miserable thing to debug.
        """
        data = self.all()
        for key, value in data.items():
            if hasattr(settings, key):
                try:
                    setattr(settings, key, value)
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Could not set settings.%s: %s", key, exc)
            os.environ[key] = value
        if data:
            logger.info("Credential vault applied: %s", ", ".join(sorted(data)))

    # -- publish target --------------------------------------------------

    def publish_mode(self) -> str:
        """Which channel finished videos go to.

        Defaults to this deployment's own channel so a first-time visitor can
        publish without setting up a Google Cloud project - which is most of
        them, and the difference between trying the tool and bouncing off it.
        """
        mode = self.get("PUBLISH_MODE") or PUBLISH_DEFAULT
        return mode if mode in (PUBLISH_DEFAULT, PUBLISH_OWN) else PUBLISH_DEFAULT

    def set_publish_mode(self, mode: str) -> str:
        if mode not in (PUBLISH_DEFAULT, PUBLISH_OWN):
            raise ValueError(f"Unknown publish mode: {mode!r}")
        self.save({"PUBLISH_MODE": mode})
        return mode

    # -- reporting -------------------------------------------------------

    @staticmethod
    def _hint(value: str) -> str:
        """A tail fragment - enough to tell two keys apart, and no more."""
        if not value:
            return ""
        if len(value) <= 8:
            return "*" * len(value)
        return f"...{value[-4:]}"

    def describe(self) -> Dict[str, Any]:
        """Everything the settings screen needs, and no secret values.

        `source` is the useful column: it says whether a value came from the
        dashboard or from an env var set at deploy time, which is the first
        question anyone asks when a key is not behaving.
        """
        vault = self.all(refresh=True)
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for field in FIELDS:
            env_value = (os.environ.get(field.key) or "").strip()
            vault_value = vault.get(field.key, "")
            # A value the vault itself pushed into the environment is not
            # "from env" - it only looks that way because apply_to_settings ran.
            from_env = bool(env_value) and not vault_value
            value = vault_value or env_value
            groups.setdefault(field.group, []).append({
                "key": field.key,
                "label": field.label,
                "help": field.help_text,
                "secret": field.secret,
                "required": field.required,
                "placeholder": field.placeholder,
                "docs_url": field.docs_url,
                "configured": bool(value),
                "hint": self._hint(value) if field.secret else value,
                "source": "vault" if vault_value else ("env" if from_env else None),
            })
        return {
            "groups": [{"name": name, "fields": fields} for name, fields in groups.items()],
            "storage_ready": self._storage_ready(),
            "error": self._load_error,
        }

    @staticmethod
    def _storage_ready() -> bool:
        from app.services.storage_service import storage
        return bool(storage.available)


vault = CredentialVault()
