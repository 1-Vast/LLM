"""MAESTRO application layer: interaction, context, tools, and run orchestration.

File summary
- Path: src/agent/__init__.py
- Purpose: Re-export the agent's interaction, context, knowledge, and orchestration pieces.
- Core points:
  - Holds the orchestrator, planner, interpreters, memory, and tool routing.
  - Consumers import the bounded run loop and its typed records from here.
- Interfaces: `MAESTROOrchestrator`, `MechanismContrastPlanner`, `CaseStore`, `MemoryStore`, `ToolRouter`, model classes
- Depends on: agent.cases, agent.context, agent.knowledge, agent.llm, agent.memory, agent.orchestrator, agent.planner, agent.reflection, agent.tool_runtime, agent.vision
"""

from .cases import CaseSnapshot, CaseState, CaseStore, MeasurementResult, ResultImport
from .context import ContextBuilder, ContextPacket, TaskIntent, TaskInterpreter
from .knowledge import EvidenceLedger, KnowledgeBase
from .llm import DeepSeekChatClient, LLMError
from .memory import EpistemicStatus, MemoryKind, MemoryScope, MemoryStore
from .orchestrator import MAESTROCaseLoop, MAESTROOrchestrator, MAESTROTurn
from .planner import LLMRepairDraft, MechanismContrastPlanner
from .reflection import ReflectionRecord
from .tool_runtime import FailureTrace, LocalToolCatalog, ToolBudget, ToolExecution, ToolReceipt, ToolRouter, ToolRuntimeError
from .decision_critic import CritiqueOutcome, TypedDecisionCritic
from .typesafe import JevEvaluation, TypeSafeJevClient, TypeSafeSettings, TypedAnswer, TypedQuestion
from .vision import VisualInspection, VisualInspector

__all__ = [
    "ContextBuilder",
    "ContextPacket",
    "CaseSnapshot",
    "CaseState",
    "CaseStore",
    "DeepSeekChatClient",
    "EpistemicStatus",
    "EvidenceLedger",
    "KnowledgeBase",
    "LLMError",
    "LLMRepairDraft",
    "LocalToolCatalog",
    "MAESTROOrchestrator",
    "MAESTROCaseLoop",
    "MAESTROTurn",
    "MemoryKind",
    "MemoryScope",
    "MemoryStore",
    "MechanismContrastPlanner",
    "MeasurementResult",
    "ResultImport",
    "ReflectionRecord",
    "TaskIntent",
    "TaskInterpreter",
    "ToolExecution",
    "ToolBudget",
    "ToolReceipt",
    "FailureTrace",
    "ToolRouter",
    "ToolRuntimeError",
    "VisualInspection",
    "VisualInspector",
    "CritiqueOutcome",
    "TypedDecisionCritic",
    "TypeSafeJevClient",
    "TypeSafeSettings",
    "TypedAnswer",
    "TypedQuestion",
    "JevEvaluation",
]
