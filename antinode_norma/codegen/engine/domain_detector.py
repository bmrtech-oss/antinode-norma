"""Domain detection from feature file content."""

from typing import List, Tuple
from antinode_norma.codegen.engine.prompt_library import Domain


class DomainDetector:
    """Auto-detect domain from feature file content based on keywords."""

    # Domain keyword signatures (lowercase)
    DOMAIN_KEYWORDS = {
        Domain.ECOMMERCE: [
            "cart",
            "checkout",
            "payment",
            "order",
            "product",
            "shipping",
            "purchase",
            "add to cart",
            "remove from cart",
            "coupon",
            "discount",
            "price",
            "inventory",
        ],
        Domain.SAAS: [
            "login",
            "logout",
            "sign in",
            "sign up",
            "dashboard",
            "settings",
            "account",
            "workspace",
            "team",
            "profile",
            "authentication",
            "permission",
            "invite",
        ],
        Domain.FINTECH: [
            "balance",
            "transfer",
            "deposit",
            "withdrawal",
            "account",
            "transaction",
            "statement",
            "payment",
            "bank",
            "money",
            "credit",
            "debit",
            "amount",
        ],
    }

    @staticmethod
    def detect_domain(feature_content: str) -> Tuple[Domain, float]:
        """
        Detect domain from feature file text.

        Args:
            feature_content: Full text content of feature file

        Returns:
            Tuple of (domain, confidence: 0.0-1.0)
            Confidence < 0.3 defaults to GENERIC domain
        """
        if not feature_content:
            return Domain.GENERIC, 0.0

        content_lower = feature_content.lower()
        scores = {domain: 0 for domain in DomainDetector.DOMAIN_KEYWORDS}

        # Count keyword matches per domain
        for domain, keywords in DomainDetector.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                # Count occurrences (case-insensitive)
                score = content_lower.count(keyword.lower())
                scores[domain] += score

        # Find highest scoring domain
        max_domain = max(
            scores, key=scores.get
        )  # Domain with highest score
        max_score = scores[max_domain]

        # Calculate total matches to compute confidence
        total_matches = sum(scores.values())

        if total_matches == 0:
            return Domain.GENERIC, 0.0

        # Confidence = (max_score / total_matches) normalized to 0-1
        confidence = min(1.0, max_score / (total_matches + 1))

        # Default to GENERIC if confidence is too low
        if confidence < 0.3:
            return Domain.GENERIC, confidence

        return max_domain, confidence

    @staticmethod
    def detect_from_features(features: List[str]) -> Tuple[Domain, float]:
        """
        Detect domain from list of feature descriptions.

        Args:
            features: List of feature step descriptions

        Returns:
            Tuple of (domain, confidence: 0.0-1.0)
        """
        if not features:
            return Domain.GENERIC, 0.0

        # Combine all features into single text
        combined_text = " ".join(features)
        return DomainDetector.detect_domain(combined_text)

    @staticmethod
    def get_domain_keywords(domain: Domain) -> List[str]:
        """
        Get keywords for a specific domain.

        Args:
            domain: Domain enum value

        Returns:
            List of keywords
        """
        return DomainDetector.DOMAIN_KEYWORDS.get(domain, [])

    @staticmethod
    def keyword_match_count(feature_content: str, domain: Domain) -> int:
        """
        Count keyword matches for a specific domain.

        Args:
            feature_content: Feature file content
            domain: Domain to check

        Returns:
            Number of keyword matches
        """
        if not feature_content or domain not in DomainDetector.DOMAIN_KEYWORDS:
            return 0

        content_lower = feature_content.lower()
        count = 0

        for keyword in DomainDetector.DOMAIN_KEYWORDS[domain]:
            count += content_lower.count(keyword.lower())

        return count
