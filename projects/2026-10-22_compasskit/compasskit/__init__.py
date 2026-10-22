"""compasskit: reference implementation of the compass primitives.

Standard library only. Each module implements one or more primitives from compass/compass.json
and names them in its docstring; `compasskit.audit` checks a whole deployment against the
compass. None of it certifies that a system is safe: each primitive is a design rule with a
falsifier, and this package implements the rule, not the proof.
"""

__version__ = "0.1.0"

from .spec import Compass, load, contract_validator, compass_validator, prompt_text, CONTRACTS
from .schema import Validator, SchemaError
from .beliefs import Belief, BeliefStore, BeliefError, standpoint_register, assertion_check
from .inference import InferenceRecord, ScreenResult, screen
from .instructions import InstructionParse, Decision, decide
from .absence import Absence, review_capability_report
from .identity import Registry, Segment
from .floor import Floor, FloorViolation, RegisterError
from .ledger import Ledger, LedgerError
from .authority import sign_link, verify_chain, ObjectionBoard, checker_weight
from .audit import audit, Finding
from .runtime import GovernedAgent, Proposal, Tool, StepResult

__all__ = [
    "__version__", "Compass", "load", "contract_validator", "compass_validator", "prompt_text",
    "CONTRACTS", "Validator", "SchemaError", "Belief", "BeliefStore", "BeliefError",
    "standpoint_register", "assertion_check", "InferenceRecord", "ScreenResult", "screen",
    "InstructionParse", "Decision", "decide", "Absence", "review_capability_report",
    "Registry", "Segment", "Floor", "FloorViolation", "RegisterError", "Ledger", "LedgerError",
    "sign_link", "verify_chain", "ObjectionBoard", "checker_weight", "audit", "Finding",
    "GovernedAgent", "Proposal", "Tool", "StepResult",
]
