"""
Prompt Validation System
Validates prompts for correctness and efficiency.
"""
from dataclasses import dataclass
from typing import List, Dict, Any
from jinja2 import Environment, meta

from app.core.prompts.base_prompts import Prompt, PromptType
from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of prompt validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    token_estimate: int
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class PromptValidator:
    """Validates prompts for structure, syntax, and efficiency"""
    
    # Maximum prompt lengths by type (characters)
    MAX_LENGTHS = {
        PromptType.HOOK: 800,
        PromptType.SCRIPT: 3000,
        PromptType.CRITIC: 2000,
        PromptType.STRATEGY: 2500,
        PromptType.NARRATION: 1500,
        PromptType.SCENE_DESCRIPTION: 1000,
        PromptType.TITLE_GENERATION: 600,
    }
    
    # Token count warnings (estimated tokens)
    TOKEN_WARNING_THRESHOLD = 3000
    TOKEN_MAX_THRESHOLD = 6000
    
    def __init__(self):
        self.env = Environment()
    
    def validate(self, prompt: Prompt) -> ValidationResult:
        """
        Validate a prompt comprehensively.
        
        Args:
            prompt: Prompt to validate
            
        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []
        
        # 1. Validate length
        length_errors = self._validate_length(prompt)
        errors.extend(length_errors)
        
        # 2. Validate template syntax
        syntax_errors = self._validate_syntax(prompt)
        errors.extend(syntax_errors)
        
        # 3. Validate variables presence
        var_errors = self._validate_variables(prompt)
        errors.extend(var_errors)
        
        # 4. Estimate tokens and warn if excessive
        token_estimate = self._estimate_tokens(prompt.template)
        token_warnings = self._check_token_count(token_estimate)
        warnings.extend(token_warnings)
        
        # 5. Check for common issues
        quality_warnings = self._check_quality(prompt)
        warnings.extend(quality_warnings)
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.warning(
                f"Prompt validation failed for {prompt.id}",
                extra={"prompt_id": prompt.id, "errors": errors}
            )
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            token_estimate=token_estimate
        )
    
    def _validate_length(self, prompt: Prompt) -> List[str]:
        """Validate prompt template length"""
        errors = []
        
       max_length = self.MAX_LENGTHS.get(prompt.type, 2000)
        
        if len(prompt.template) > max_length:
            errors.append(
                f"Template too long: {len(prompt.template)} chars (max {max_length} for {prompt.type.value})"
            )
        
        if len(prompt.template) < 50:
            errors.append("Template too short: minimum 50 characters")
        
        return errors
    
    def _validate_syntax(self, prompt: Prompt) -> List[str]:
        """Validate Jinja2 template syntax"""
        errors = []
        
        try:
            self.env.parse(prompt.template)
        except Exception as e:
            errors.append(f"Template syntax error: {str(e)}")
        
        return errors
    
    def _validate_variables(self, prompt: Prompt) -> List[str]:
        """Validate that declared variables match template"""
        errors = []
        
        try:
            # Parse template to find variables
            ast = self.env.parse(prompt.template)
            template_vars = meta.find_undeclared_variables(ast)
            
            # Check for undeclared variables in prompt.variables
            declared_vars = set(prompt.variables)
            used_vars = template_vars
            
            # Variables used but not declared
            undeclared = used_vars - declared_vars
            if undeclared:
                errors.append(
                    f"Variables used but not declared: {', '.join(undeclared)}"
                )
            
            # Variables declared but not used (warning only)
            unused = declared_vars - used_vars
            if unused:
                # This is a warning, not an error
                pass
                
        except Exception as e:
            errors.append(f"Failed to parse template variables: {str(e)}")
        
        return errors
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count.
        Rough estimate: 1 token ≈ 4 characters
        """
        return len(text) // 4
    
    def _check_token_count(self, token_estimate: int) -> List[str]:
        """Check if token count is concerning"""
        warnings = []
        
        if token_estimate > self.TOKEN_MAX_THRESHOLD:
            warnings.append(
                f"Token count very high ({token_estimate}). Consider splitting prompt."
            )
        elif token_estimate > self.TOKEN_WARNING_THRESHOLD:
            warnings.append(
                f"Token count high ({token_estimate}). May increase cost."
            )
        
        return warnings
    
    def _check_quality(self, prompt: Prompt) -> List[str]:
        """Check for common quality issues"""
        warnings = []
        
        template_lower = prompt.template.lower()
        
        # Check for vague instructions
        if "be creative" in template_lower or "do your best" in template_lower:
            warnings.append("Prompt contains vague instructions. Be more specific.")
        
        # Check for conflicting instructions
        if "always" in template_lower and "never" in template_lower:
            warnings.append("Prompt may contain conflicting instructions.")
        
        # Check for proper JSON formatting instruction if applicable
        if "json" in template_lower and "format" not in template_lower:
            warnings.append("JSON output requested but format not specified.")
        
        return warnings
    
    def validate_template_only(self, template_str: str) -> ValidationResult:
        """Validate just a template string (for ad-hoc validation)"""
        errors = []
        warnings = []
        
        try:
            self.env.parse(template_str)
        except Exception as e:
            errors.append(f"Template syntax error: {str(e)}")
        
        token_estimate = self._estimate_tokens(template_str)
        token_warnings = self._check_token_count(token_estimate)
        warnings.extend(token_warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            token_estimate=token_estimate
        )


# Global validator
validator = PromptValidator()
