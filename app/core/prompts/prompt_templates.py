"""
Prompt Template Rendering
Jinja2-based template system for prompt generation.
"""
from jinja2 import Template, TemplateSyntaxError, Environment, StrictUndefined
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.core.prompts.base_prompts import Prompt, PromptType
from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RenderedPrompt:
    """Result of prompt rendering"""
    prompt_id: str
    rendered_text: str
    variables_used: Dict[str, Any]
    token_estimate: int
    

class PromptRenderer:
    """
    Renders prompt templates with Jinja2.
    Supports variable substitution and validation.
    """
    
    def __init__(self):
        # Create Jinja2 environment with strict undefined handling
        self.env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render(
        self,
        prompt: Prompt,
        **variables
    ) -> RenderedPrompt:
        """
        Render a prompt template with provided variables.
        
        Args:
            prompt: Prompt to render
            **variables: Template variables
            
        Returns:
            RenderedPrompt with rendered text
            
        Raises:
            ValidationError if template rendering fails
        """
        # Validate required variables
        missing_vars = set(prompt.variables) - set(variables.keys())
        if missing_vars:
            raise ValidationError(
                f"Missing required variables for prompt {prompt.id}",
                details={
                    "missing_variables": list(missing_vars),
                    "provided": list(variables.keys()),
                    "required": prompt.variables
                }
            )
        
        try:
            # Render template
            template = self.env.from_string(prompt.template)
            rendered = template.render(**variables)
            
            # Estimate token count (rough: 1 token ≈ 4 characters)
            token_estimate = len(rendered) // 4
            
            logger.debug(
                f"Rendered prompt {prompt.id}",
                extra={
                    "prompt_id": prompt.id,
                    "variables": list(variables.keys()),
                    "token_estimate": token_estimate
                }
            )
            
            return RenderedPrompt(
                prompt_id=prompt.id,
                rendered_text=rendered,
                variables_used=variables,
                token_estimate=token_estimate
            )
            
        except TemplateSyntaxError as e:
            raise ValidationError(
                f"Template syntax error in prompt {prompt.id}",
                details={"error": str(e), "line": e.lineno}
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to render prompt {prompt.id}",
                details={"error": str(e)}
            )
    
    def render_by_id(
        self,
        prompt_id: str,
        **variables
    ) -> RenderedPrompt:
        """Render prompt by ID from registry"""
        from app.core.prompts.base_prompts import get_prompt
        
        prompt = get_prompt(prompt_id)
        if not prompt:
            raise ValidationError(
                f"Prompt not found: {prompt_id}",
                details={"prompt_id": prompt_id}
            )
        
        return self.render(prompt, **variables)
    
    def validate_template(self, template_str: str) -> bool:
        """
        Validate Jinja2 template syntax without rendering.
        
        Args:
            template_str: Template string to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError if invalid
        """
        try:
            self.env.from_string(template_str)
            return True
        except TemplateSyntaxError as e:
            raise ValidationError(
                "Invalid template syntax",
                details={"error": str(e), "line": e.lineno}
            )


# Global renderer instance
renderer = PromptRenderer()


# Convenience functions
def render_prompt(prompt: Prompt, **variables) -> str:
    """Render a prompt and return text"""
    result = renderer.render(prompt, **variables)
    return result.rendered_text


def render_prompt_by_id(prompt_id: str, **variables) -> str:
    """Render a prompt by ID and return text"""
    result = renderer.render_by_id(prompt_id, **variables)
    return result.rendered_text
