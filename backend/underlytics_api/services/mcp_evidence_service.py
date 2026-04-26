from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from underlytics_api.models.application import Application
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.user import User

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "mcp_fixtures" / "public_registry_fixture.json"
)

POLICY_RULES_BY_PRODUCT_CODE: dict[str, dict[str, Any]] = {
    "personal_loan": {
        "policy_version": "2026-04",
        "approval_requirements": [
            "requested_amount_within_product_range",
            "requested_term_within_product_range",
        ],
        "manual_review_triggers": [
            "missing_policy_context",
            "amount_or_term_near_limit",
        ],
        "product_specific_rules": [],
    },
    "salary_advance": {
        "policy_version": "2026-04",
        "approval_requirements": [
            "requested_amount_within_product_range",
            "requested_term_within_product_range",
            "employment_status_should_indicate_employed",
        ],
        "manual_review_triggers": [
            "employment_status_missing",
            "employment_status_not_employed",
        ],
        "product_specific_rules": [
            "salary_advance_is_best_suited_to_employed_applicants",
        ],
    },
    "small_business_loan": {
        "policy_version": "2026-04",
        "approval_requirements": [
            "requested_amount_within_product_range",
            "requested_term_within_product_range",
            "business_or_self_employed_context_should_be_present",
        ],
        "manual_review_triggers": [
            "employer_or_business_name_missing",
            "employment_status_missing",
        ],
        "product_specific_rules": [
            "small_business_loan_requires_some_business_context",
        ],
    },
}


def _normalize_name(value: str | None) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower())
    return " ".join(normalized.split())


@lru_cache(maxsize=1)
def _load_public_registry_fixture() -> dict[str, dict[str, Any]]:
    if not FIXTURE_PATH.exists():
        return {}

    raw = json.loads(FIXTURE_PATH.read_text())
    return {
        _normalize_name(entry.get("lookup_key") or entry.get("registered_name")): entry
        for entry in raw
        if isinstance(entry, dict)
    }


def _build_policy_knowledgebase_evidence(
    *,
    application: Application,
    product: LoanProduct | None,
) -> dict[str, Any]:
    if not product:
        return {
            "tool_name": "policy_knowledgebase",
            "status": "skipped",
            "source": "internal_policy_catalog",
            "cost_tier": "free",
            "requires_api_key": False,
            "reason": "loan_product_missing",
            "evidence": {},
        }

    policy_rules = POLICY_RULES_BY_PRODUCT_CODE.get(
        product.code,
        {
            "policy_version": "2026-04",
            "approval_requirements": [
                "requested_amount_within_product_range",
                "requested_term_within_product_range",
            ],
            "manual_review_triggers": ["missing_policy_context"],
            "product_specific_rules": [],
        },
    )

    amount_near_upper_limit = application.requested_amount >= int(product.max_amount * 0.9)
    term_near_upper_limit = (
        application.requested_term_months >= int(product.max_term_months * 0.9)
    )

    return {
        "tool_name": "policy_knowledgebase",
        "status": "completed",
        "source": "internal_policy_catalog",
        "cost_tier": "free",
        "requires_api_key": False,
        "evidence": {
            "policy_version": policy_rules["policy_version"],
            "product_code": product.code,
            "product_active": product.is_active,
            "approval_requirements": policy_rules["approval_requirements"],
            "manual_review_triggers": policy_rules["manual_review_triggers"],
            "product_specific_rules": policy_rules["product_specific_rules"],
            "computed_checks": {
                "amount_within_range": product.min_amount
                <= application.requested_amount
                <= product.max_amount,
                "term_within_range": product.min_term_months
                <= application.requested_term_months
                <= product.max_term_months,
                "amount_near_upper_limit": amount_near_upper_limit,
                "term_near_upper_limit": term_near_upper_limit,
            },
        },
    }


def _build_public_registry_evidence(
    *,
    application: Application,
    applicant: User | None,
) -> dict[str, Any]:
    employer_name = application.employer_name
    applicant_name = applicant.full_name if applicant else None

    if not employer_name:
        return {
            "tool_name": "public_registry_lookup",
            "status": "skipped",
            "source": "fixture_public_registry",
            "cost_tier": "free",
            "requires_api_key": False,
            "reason": "employer_name_missing",
            "evidence": {
                "lookup_target": "employer",
                "query": None,
                "expected_entity_name": employer_name,
                "applicant_name": applicant_name,
                "comparison_rule": "No employer lookup was performed.",
            },
        }

    registry = _load_public_registry_fixture()
    normalized_employer_name = _normalize_name(employer_name)
    match = registry.get(normalized_employer_name)

    email_domain = None
    if applicant and applicant.email and "@" in applicant.email:
        email_domain = applicant.email.split("@", 1)[1].lower()

    base_evidence = {
        "lookup_target": "employer",
        "query": employer_name,
        "expected_entity_name": employer_name,
        "applicant_name": applicant_name,
        "email_domain": email_domain,
        "comparison_rule": (
            "Compare registry results against expected_entity_name only. "
            "Do not compare employer lookup results against applicant_name."
        ),
    }

    if not match:
        return {
            "tool_name": "public_registry_lookup",
            "status": "completed",
            "source": "fixture_public_registry",
            "cost_tier": "free",
            "requires_api_key": False,
            "evidence": {
                **base_evidence,
                "match_found": False,
                "registry_status": "not_found",
            },
        }

    registered_name = match["registered_name"]
    normalized_registered_name = _normalize_name(registered_name)

    return {
        "tool_name": "public_registry_lookup",
        "status": "completed",
        "source": "fixture_public_registry",
        "cost_tier": "free",
        "requires_api_key": False,
        "evidence": {
            **base_evidence,
            "match_found": True,
            "registered_name": registered_name,
            "registered_name_matches_query": (
                normalized_registered_name == normalized_employer_name
            ),
            "registry_status": match["status"],
            "entity_type": match["entity_type"],
            "jurisdiction": match["jurisdiction"],
            "website_domain": match.get("website_domain"),
        },
    }


def build_mcp_tool_evidence(
    db: Session,
    *,
    application: Application,
    agent_name: str,
) -> list[dict[str, Any]]:
    if agent_name == "policy_retrieval":
        product = (
            db.query(LoanProduct)
            .filter(LoanProduct.id == application.loan_product_id)
            .first()
        )
        return [_build_policy_knowledgebase_evidence(application=application, product=product)]

    if agent_name == "fraud_verification":
        applicant = db.query(User).filter(User.id == application.applicant_user_id).first()
        return [_build_public_registry_evidence(application=application, applicant=applicant)]

    return []