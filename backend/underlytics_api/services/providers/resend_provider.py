from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class EmailDeliveryResult:
    provider_name: str
    provider_message_id: str | None


class ResendProvider:
    def __init__(self, *, api_key: str, email_from: str, timeout_seconds: int = 15):
        self.api_key = api_key
        self.email_from = email_from
        self.timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "resend"

    def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> EmailDeliveryResult:
        payload = json.dumps(
            {
                "from": self.email_from,
                "to": [to_email],
                "subject": subject,
                "html": html_body,
            }
        ).encode("utf-8")

        request = Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "underlytics-api/1.0",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))

            return EmailDeliveryResult(
                provider_name=self.provider_name,
                provider_message_id=response_payload.get("id"),
            )

        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Resend API error {exc.code}: {error_body}") from exc

        except URLError as exc:
            raise RuntimeError(f"Resend network error: {exc.reason}") from exc