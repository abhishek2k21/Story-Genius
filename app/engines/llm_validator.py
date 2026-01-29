"""
LLM Output Validator
Validates and parses LLM responses with Pydantic.
"""
import json
import re
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMValidator:
    """
    Validates LLM outputs using Pydantic models.
    Handles JSON parsing with fallback strategies.
    """
    
    def validate_json(
        self,
        response: str,
        model: Type[T],
        strict: bool = False
    ) -> T:
        """
        Parse and validate LLM JSON response.
        
        Args:
            response: LLM response text
            model: Pydantic model to validate against
            strict: If True, raise error on validation failure
            
        Returns:
            Validated model instance
            
        Raises:
            ValidationError if parsing/validation fails and strict=True
        """
        # Try direct JSON parsing
        try:
            data = json.loads(response)
            return model(**data)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code blocks
            data = self._extract_json_from_markdown(response)
            if data:
                try:
                    return model(**data)
                except PydanticValidationError as e:
                    if strict:
                        raise ValidationError(
                            "LLM response validation failed",
                            details={"errors": e.errors()}
                        )
                    # Return partial data with defaults
                    return self._create_partial_model(model, data)
        except PydanticValidationError as e:
            if strict:
                raise ValidationError(
                    "LLM response validation failed",
                    details={"errors": e.errors()}
                )
            # Try to create model with available fields
            return self._create_partial_model(model, {})
        
        # Last resort: empty model
        if strict:
            raise ValidationError(
                "Failed to parse LLM response as JSON",
                details={"response_preview": response[:200]}
            )
        
        logger.warning(
            "Failed to parse LLM response, returning default model",
            extra={"model": model.__name__}
        )
        return model()
    
    def _extract_json_from_markdown(self, text: str) -> Optional[Dict]:
        """Extract JSON from markdown code blocks"""
        # Look for ```json ... ``` blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Look for ``` ... ``` blocks
        code_match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Look for { ... } directly in text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _create_partial_model(self, model: Type[T], data: Dict) -> T:
        """Create model with partial data, using defaults for missing fields"""
        try:
            return model(**data)
        except PydanticValidationError:
            # Get model defaults
            return model()
    
    def extract_field(
        self,
        response: str,
        field_name: str,
        default: Any = None
    ) -> Any:
        """
        Extract a single field from LLM response.
        
        Args:
            response: LLM response text
            field_name: Field to extract
            default: Default value if not found
            
        Returns:
            Field value or default
        """
        try:
            data = json.loads(response)
            return data.get(field_name, default)
        except json.JSONDecodeError:
            # Try markdown extraction
            data = self._extract_json_from_markdown(response)
            if data:
                return data.get(field_name, default)
        
        return default


# Global validator
llm_validator = LLMValidator()
