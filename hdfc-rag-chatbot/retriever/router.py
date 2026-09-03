import re
from enum import Enum
from typing import Dict, Tuple

class QueryIntent(Enum):
    DIRECT_LOOKUP = "DIRECT_LOOKUP"
    COMPARATIVE = "COMPARATIVE"
    PORTFOLIO_HOLDING = "PORTFOLIO_HOLDING"
    GUIDANCE = "GUIDANCE"

class QueryRouter:
    def __init__(self):
        # Direct lookup keywords
        self.direct_lookup_pattern = re.compile(r'\b(nav|aum|expense ratio|sip|minimum sip|rating|returns|return|%)\b', re.IGNORECASE)
        # Comparative keywords
        self.comparative_pattern = re.compile(r'\b(vs|compare|better|higher|lower|difference|between)\b', re.IGNORECASE)
        # Portfolio/Holding keywords
        self.portfolio_pattern = re.compile(r'\b(hold|holds|holding|holdings|invest|invests|invested|stock|company|sector)\b', re.IGNORECASE)

    def classify_intent(self, query: str) -> QueryIntent:
        # Check comparative first as it often contains direct lookup keywords (e.g. "compare NAV")
        if self.comparative_pattern.search(query):
            return QueryIntent.COMPARATIVE
            
        if self.direct_lookup_pattern.search(query):
            return QueryIntent.DIRECT_LOOKUP
            
        if self.portfolio_pattern.search(query):
            return QueryIntent.PORTFOLIO_HOLDING
            
        # Default to guidance for everything else
        return QueryIntent.GUIDANCE

    def get_weights(self, intent: QueryIntent) -> Tuple[float, float]:
        """Returns (dense_weight, sparse_weight) based on intent"""
        if intent == QueryIntent.DIRECT_LOOKUP:
            return 0.2, 0.8
        elif intent == QueryIntent.COMPARATIVE:
            return 0.5, 0.5
        elif intent in (QueryIntent.PORTFOLIO_HOLDING, QueryIntent.GUIDANCE):
            return 0.8, 0.2
        return 0.5, 0.5 # Default fallback
