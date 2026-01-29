"""
Unit Tests for Prompt System
"""
import pytest
from jinja2 import TemplateSyntaxError

from app.core.prompts.base_prompts import Prompt, PromptType, get_prompt, list_prompts
from app.core.prompts.prompt_templates import renderer, render_prompt
from app.core.prompts.prompt_validation import validator
from app.core.prompts.prompt_versioning import version_manager
from app.core.exceptions import ValidationError


# ========== Base Prompts Tests ==========

@pytest.mark.unit
def test_get_prompt_by_id():
    """Test retrieving prompt by ID"""
    prompt = get_prompt("hook_v1")
    assert prompt is not None
    assert prompt.type == PromptType.HOOK
    assert "platform" in prompt.variables


@pytest.mark.unit
def test_get_nonexistent_prompt():  """Test retrieving non-existent prompt"""
    prompt = get_prompt("nonexistent")
    assert prompt is None


@pytest.mark.unit
def test_list_prompts_all():
    """Test listing all prompts"""
    prompts = list_prompts()
    assert len(prompts) >= 5  # We have 5+ base prompts
    

@pytest.mark.unit
def test_list_prompts_by_type():
    """Test filtering prompts by type"""
    hook_prompts = list_prompts(PromptType.HOOK)
    assert all(p.type == PromptType.HOOK for p in hook_prompts)


# ========== Template Rendering Tests ==========

@pytest.mark.unit
def test_render_prompt_success(test_prompt, test_prompt_variables):
    """Test successful prompt rendering"""
    result = renderer.render(test_prompt, **test_prompt_variables)
    
    assert result.prompt_id == test_prompt.id
    assert "youtube_shorts" in result.rendered_text
    assert "artificial intelligence" in result.rendered_text
    assert result.token_estimate > 0


@pytest.mark.unit
def test_render_prompt_missing_variable(test_prompt):
    """Test rendering with missing variables"""
    with pytest.raises(ValidationError) as exc:
        renderer.render(test_prompt, platform="youtube")  # Missing 'topic'
    
    assert "missing" in str(exc.value.message).lower()


@pytest.mark.unit
def test_render_prompt_by_id():
    """Test rendering prompt by ID"""
    result = renderer.render_by_id(
        "hook_v1",
        platform="youtube_shorts",
        genre="horror",
        audience="teens",
        tone="suspenseful",
        duration=60
    )
    
    assert "youtube_shorts" in result.rendered_text
    assert "horror" in result.rendered_text


@pytest.mark.unit
def test_validate_template_syntax_valid():
    """Test valid template syntax"""
    valid_template = "Hello {{name}}, welcome to {{platform}}"
    assert renderer.validate_template(valid_template) is True


@pytest.mark.unit
def test_validate_template_syntax_invalid():
    """Test invalid template syntax"""
    invalid_template = "Hello {{name}, missing close"
    
    with pytest.raises(ValidationError):
        renderer.validate_template(invalid_template)


# ========== Prompt Validation Tests ==========

@pytest.mark.unit
def test_validate_prompt_success(test_prompt):
    """Test successful prompt validation"""
    result = validator.validate(test_prompt)
    
    assert result.is_valid
    assert len(result.errors) == 0
    assert result.token_estimate > 0


@pytest.mark.unit
def test_validate_prompt_too_long():
    """Test prompt exceeding length limit"""
    long_prompt = Prompt(
        id="long_test",
        name="Too Long",
        type=PromptType.HOOK,
        template="x" * 1000,  # Exceeds 800 char limit for hooks
        version="1.0",
        variables=[]
    )
    
    result = validator.validate(long_prompt)
    assert not result.is_valid
    assert any("too long" in err.lower() for err in result.errors)


@pytest.mark.unit
def test_validate_prompt_undeclared_variables():
    """Test prompt with undeclared variables"""
    prompt = Prompt(
        id="test",
        name="Test",
        type=PromptType.HOOK,
        template="Hello {{name}} from {{city}}",  # city not declared
        version="1.0",
        variables=["name"]  # Only name declared
    )
    
    result = validator.validate(prompt)
    assert not result.is_valid
    assert any("not declared" in err.lower() for err in result.errors)


@pytest.mark.unit
def test_token_count_estimation():
    """Test token count estimation"""
    text = "a" * 400  # 400 characters
    token_count = validator._estimate_tokens(text)
    
    # Should be around 100 tokens (400/4)
    assert 80 <= token_count <= 120


# ========== Versioning Tests ==========

@pytest.mark.unit
def test_create_version():
    """Test creating a new version"""
    version = version_manager.create_version(
        prompt_id="test_prompt",
        version="1.0",
        template="Test template",
        author="test_user"
    )
    
    assert version.prompt_id == "test_prompt"
    assert version.version == "1.0"
    assert version.author == "test_user"


@pytest.mark.unit
def test_get_version():
    """Test retrieving specific version"""
    # Create version first
    version_manager.create_version(
        prompt_id="test_v2",
        version="1.0",
        template="V1 template"
    )
    
    # Retrieve it
    retrieved = version_manager.get_version("test_v2", "1.0")
    assert retrieved is not None
    assert retrieved.version == "1.0"


@pytest.mark.unit
def test_get_latest_version():
    """Test getting latest version"""
    # Create multiple versions
    version_manager.create_version("test_multi", "1.0", "V1")
    version_manager.create_version("test_multi", "1.1", "V1.1")
    version_manager.create_version("test_multi", "2.0", "V2")
    
    latest = version_manager.get_latest_version("test_multi")
    assert latest.version == "2.0"


@pytest.mark.unit
def test_version_rollback():
    """Test rolling back to previous version"""
    # Create versions
    version_manager.create_version("test_rollback", "1.0", "Old template")
    version_manager.create_version("test_rollback", "2.0", "New template")
    
    # Rollback to 1.0
    success = version_manager.rollback("test_rollback", "1.0")
    assert success
    
    # Latest should be new version with old template
    latest = version_manager.get_latest_version("test_rollback")
    assert "Old template" in latest.template


@pytest.mark.unit
def test_compare_versions():
    """Test version comparison"""
    version_manager.create_version("test_compare", "1.0", "Template A")
    version_manager.create_version("test_compare", "2.0", "Template B")
    
    comparison = version_manager.compare_versions("test_compare", "1.0", "2.0")
    
    assert comparison["prompt_id"] == "test_compare"
    assert comparison["version1"]["version"] == "1.0"
    assert comparison["version2"]["version"] == "2.0"
    assert comparison["diff"]["template_changed"] is True
