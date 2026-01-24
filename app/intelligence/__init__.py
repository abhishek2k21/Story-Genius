# Intelligence Package - Audience/Emotion/Persona Services + Path 1 Thinking Modules

# Week 13 - Path 1: Thinking Modules
from app.intelligence.assumptions import (
    AssumptionExtractor,
    extract_assumptions,
    get_assumption_extractor
)
from app.intelligence.counter import (
    CounterArgumentEngine,
    generate_counter_arguments,
    get_counter_engine
)
from app.intelligence.second_order import (
    SecondOrderChecker,
    analyze_second_order_effects,
    get_second_order_checker
)
from app.intelligence.depth_scorer import (
    DepthScorer,
    score_idea_depth,
    get_depth_scorer
)
from app.intelligence.synthesis import (
    SynthesisEngine,
    synthesize_stronger_idea,
    get_synthesis_engine
)

__all__ = [
    # Assumption Extractor
    "AssumptionExtractor",
    "extract_assumptions",
    "get_assumption_extractor",
    # Counter-Argument Engine
    "CounterArgumentEngine",
    "generate_counter_arguments",
    "get_counter_engine",
    # Second-Order Checker
    "SecondOrderChecker",
    "analyze_second_order_effects",
    "get_second_order_checker",
    # Depth Scorer
    "DepthScorer",
    "score_idea_depth",
    "get_depth_scorer",
    # Synthesis Engine
    "SynthesisEngine",
    "synthesize_stronger_idea",
    "get_synthesis_engine",
    # Week 14 - Path 1 Runner
    "Path1Runner",
    "Path1Mode",
    "TrustThresholds",
    "get_path1_runner",
    "analyze_idea",
    "filter_ideas",
]

# Week 14 - Path 1 Integrated Runner
from app.intelligence.path1_runner import (
    Path1Runner,
    Path1Mode,
    TrustThresholds,
    get_path1_runner,
    analyze_idea,
    filter_ideas
)
