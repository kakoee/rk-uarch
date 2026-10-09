"""Accepted uarch contract 0.2; historical 0.1 inspection is explicitly named."""

from .common import CONTRACT_VERSION, RK_SCHEMA_SNAPSHOT
from .hardware import HardwareSpec
from .model_card import ModelCard
from .model_shape import ModelShape, ModelSpec, check_parity, implied_params
from .operators import OpSpec
from .precision import Precision, PrecisionFormat
from .request import CharacterizationRequest
from .sourced import Calibration, SourcedValue
from .table import Row, UarchCostTable

__all__ = [
    "CONTRACT_VERSION",
    "RK_SCHEMA_SNAPSHOT",
    "Calibration",
    "CharacterizationRequest",
    "HardwareSpec",
    "ModelCard",
    "ModelShape",
    "ModelSpec",
    "OpSpec",
    "Precision",
    "PrecisionFormat",
    "Row",
    "SourcedValue",
    "UarchCostTable",
    "check_parity",
    "implied_params",
]

from .assumptions import AssumptionSet as AssumptionSet
from .assumptions import ModelIdentity as ModelIdentity
from .comparison import ComparisonArtifact as ComparisonArtifact
from .comparison import PrecisionCheckInput as PrecisionCheckInput
from .comparison import PrecisionCheckTrace as PrecisionCheckTrace
from .comparison import PrecisionRefusalObservation as PrecisionRefusalObservation
from .comparison import ReferenceInventory as ReferenceInventory
from .derivation import Derivation as Derivation
from .derivation import DerivedParameter as DerivedParameter
from .evidence import EvidenceRecord as EvidenceRecord
from .evidence import OrderingRecord as OrderingRecord
from .evidence import ReviewRecord as ReviewRecord
from .evidence import SourceRecord as SourceRecord
from .evidence import VerificationRecord as VerificationRecord
from .exports import ComponentExport as ComponentExport
from .exports import ComponentPrecision as ComponentPrecision
from .exports import ExecutionModelInput as ExecutionModelInput
from .exports import ExportBinding as ExportBinding
from .exports import UpstreamComponentBinding as UpstreamComponentBinding
from .prepared import OpGroup as OpGroup
from .prepared import PreparedBundle as PreparedBundle
from .prepared import PreparedGraph as PreparedGraph
from .prepared import PreparedOp as PreparedOp
from .prepared import PreparedPoint as PreparedPoint
from .prepared import Producer as Producer
from .prepared import Query as Query
from .prepared import RankScope as RankScope
from .registry import FamilyRegistry as FamilyRegistry
from .report_context import DependencySelector as DependencySelector
from .report_context import MetricDependencies as MetricDependencies
from .report_context import MetricRecipe as MetricRecipe
from .report_context import RenderSpec as RenderSpec
from .report_context import ReportContext as ReportContext
from .report_context import SourceMetricRecipe as SourceMetricRecipe
from .request import LegacyCharacterizationRequest as LegacyCharacterizationRequest
from .request import RequestIntent as RequestIntent
from .table import ArtifactBindings as ArtifactBindings
from .table import LegacyUarchCostTable as LegacyUarchCostTable
from .table import OpResult as OpResult
from .table import ReportScope as ReportScope
