#!/usr/bin/env python3
"""
Extraction Metrics Infrastructure Component
==========================================

Comprehensive metrics collection and confidence scoring for extraction quality
assessment and optimization. Enables data-driven extraction improvements.

Based on IncomeTaxAI patterns for performance monitoring and quality control.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import time
import statistics
import json

from form16_extractor.models.form16_models import Form16Document


class MetricType(Enum):
    """Types of extraction metrics"""
    EXTRACTION_RATE = "extraction_rate"
    PROCESSING_TIME = "processing_time"
    CONFIDENCE_SCORE = "confidence_score"
    TABLE_UTILIZATION = "table_utilization"
    FIELD_COVERAGE = "field_coverage"
    VALIDATION_SCORE = "validation_score"
    ERROR_RATE = "error_rate"


class ExtractorComponent(Enum):
    """Extractor component types for granular metrics"""
    EMPLOYEE_EXTRACTOR = "employee"
    EMPLOYER_EXTRACTOR = "employer"
    SALARY_EXTRACTOR = "salary"
    DEDUCTIONS_EXTRACTOR = "deductions"
    TAX_EXTRACTOR = "tax"
    METADATA_EXTRACTOR = "metadata"
    QUARTERLY_TDS_EXTRACTOR = "quarterly_tds"


@dataclass
class ComponentMetrics:
    """Metrics for a single extractor component"""
    component: ExtractorComponent
    extraction_rate: float
    processing_time_ms: float
    confidence_score: float
    fields_attempted: int
    fields_extracted: int
    fields_validated: int
    validation_issues: int
    tables_processed: int
    tables_utilized: int
    errors: List[str] = field(default_factory=list)


@dataclass
class TableMetrics:
    """Metrics for table processing"""
    table_index: int
    table_type: str
    rows: int
    cols: int
    processing_time_ms: float
    utilization_rate: float  # How much of the table was used
    relevance_score: float
    extractors_used: List[str] = field(default_factory=list)


@dataclass
class ExtractionSession:
    """Complete extraction session metrics"""
    session_id: str
    file_name: str
    start_time: datetime
    end_time: Optional[datetime]
    total_processing_time_ms: float
    overall_extraction_rate: float
    overall_confidence_score: float
    component_metrics: Dict[ExtractorComponent, ComponentMetrics]
    table_metrics: List[TableMetrics]
    validation_summary: Dict[str, Any]
    performance_summary: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class ExtractionMetrics:
    """
    Infrastructure component for comprehensive extraction metrics collection.
    
    Tracks performance, quality, and utilization metrics across all extraction
    components to enable data-driven optimization and quality assessment.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_session: Optional[ExtractionSession] = None
        self.component_timers: Dict[ExtractorComponent, float] = {}
        
        # Define expected fields for each component
        self.component_fields = {
            ExtractorComponent.EMPLOYEE_EXTRACTOR: [
                'name', 'pan', 'address', 'designation', 'father_name'
            ],
            ExtractorComponent.EMPLOYER_EXTRACTOR: [
                'name', 'tan', 'address', 'pan'
            ],
            ExtractorComponent.SALARY_EXTRACTOR: [
                'basic_salary', 'hra', 'transport_allowance', 'medical_allowance',
                'special_allowance', 'overtime_allowance', 'commission_bonus',
                'perquisites_value', 'gross_salary', 'exempt_allowances', 'net_taxable_salary'
            ],
            ExtractorComponent.DEDUCTIONS_EXTRACTOR: [
                'section_80c_ppf', 'section_80c_life_insurance', 'section_80c_elss',
                'section_80c_nsc', 'section_80c_fd', 'section_80c_ulip', 'section_80c_other',
                'section_80d', 'section_80e', 'section_80g', 'section_80tta', 'section_80ttb',
                'standard_deduction', 'professional_tax', 'total_deductions'
            ],
            ExtractorComponent.TAX_EXTRACTOR: [
                'total_income', 'tax_on_total_income', 'education_cess', 'total_tax_cess',
                'rebate_section_87a', 'net_tax', 'total_tds'
            ],
            ExtractorComponent.METADATA_EXTRACTOR: [
                'certificate_number', 'assessment_year', 'pan', 'name'
            ],
            ExtractorComponent.QUARTERLY_TDS_EXTRACTOR: [
                'q1_amount', 'q2_amount', 'q3_amount', 'q4_amount'
            ]
        }
    
    def start_session(self, file_name: str) -> str:
        """Start a new extraction session"""
        session_id = f"session_{int(time.time() * 1000)}"
        
        self.current_session = ExtractionSession(
            session_id=session_id,
            file_name=file_name,
            start_time=datetime.now(),
            end_time=None,
            total_processing_time_ms=0.0,
            overall_extraction_rate=0.0,
            overall_confidence_score=0.0,
            component_metrics={},
            table_metrics=[],
            validation_summary={},
            performance_summary={},
            success=False
        )
        
        self.logger.info(f"Started extraction session: {session_id} for {file_name}")
        return session_id
    
    def start_component_timer(self, component: ExtractorComponent):
        """Start timing for a specific component"""
        self.component_timers[component] = time.time() * 1000
    
    def end_component_timer(self, component: ExtractorComponent) -> float:
        """End timing for a component and return duration"""
        if component not in self.component_timers:
            return 0.0
        
        duration = (time.time() * 1000) - self.component_timers[component]
        del self.component_timers[component]
        return duration
    
    def record_component_metrics(
        self,
        component: ExtractorComponent,
        extraction_result: Any,
        processing_time_ms: float,
        tables_processed: int = 0,
        tables_utilized: int = 0,
        validation_issues: int = 0,
        errors: Optional[List[str]] = None
    ):
        """Record metrics for a specific component"""
        if not self.current_session:
            self.logger.warning("No active session for recording component metrics")
            return
        
        # Calculate field metrics
        expected_fields = self.component_fields.get(component, [])
        fields_attempted = len(expected_fields)
        fields_extracted = self._count_extracted_fields(extraction_result, expected_fields)
        fields_validated = max(0, fields_extracted - validation_issues)
        
        # Calculate rates
        extraction_rate = fields_extracted / max(fields_attempted, 1)
        confidence_score = self._calculate_component_confidence(
            extraction_result, validation_issues, fields_extracted, fields_attempted
        )
        
        # Create component metrics
        component_metrics = ComponentMetrics(
            component=component,
            extraction_rate=extraction_rate,
            processing_time_ms=processing_time_ms,
            confidence_score=confidence_score,
            fields_attempted=fields_attempted,
            fields_extracted=fields_extracted,
            fields_validated=fields_validated,
            validation_issues=validation_issues,
            tables_processed=tables_processed,
            tables_utilized=tables_utilized,
            errors=errors or []
        )
        
        self.current_session.component_metrics[component] = component_metrics
        
        self.logger.debug(
            f"Component {component.value}: {extraction_rate:.1%} extraction, "
            f"{confidence_score:.2f} confidence, {processing_time_ms:.1f}ms"
        )
    
    def record_table_metrics(
        self,
        table_index: int,
        table_type: str,
        rows: int,
        cols: int,
        processing_time_ms: float,
        utilization_rate: float,
        relevance_score: float,
        extractors_used: List[str]
    ):
        """Record metrics for table processing"""
        if not self.current_session:
            return
        
        table_metrics = TableMetrics(
            table_index=table_index,
            table_type=table_type,
            rows=rows,
            cols=cols,
            processing_time_ms=processing_time_ms,
            utilization_rate=utilization_rate,
            relevance_score=relevance_score,
            extractors_used=extractors_used
        )
        
        self.current_session.table_metrics.append(table_metrics)
    
    def record_validation_summary(self, validation_result: Any):
        """Record validation summary metrics"""
        if not self.current_session:
            return
        
        self.current_session.validation_summary = {
            'total_issues': getattr(validation_result, 'total_issues', 0),
            'critical_issues': getattr(validation_result, 'issues_by_severity', {}).get('critical', 0),
            'error_issues': getattr(validation_result, 'issues_by_severity', {}).get('error', 0),
            'warning_issues': getattr(validation_result, 'issues_by_severity', {}).get('warning', 0),
            'confidence_score': getattr(validation_result, 'confidence_score', 0.0),
            'is_valid': getattr(validation_result, 'is_valid', False)
        }
    
    def finalize_session(self, success: bool = True, error_message: Optional[str] = None) -> ExtractionSession:
        """Finalize the current extraction session"""
        if not self.current_session:
            raise ValueError("No active session to finalize")
        
        # Set end time and calculate total duration
        self.current_session.end_time = datetime.now()
        self.current_session.total_processing_time_ms = (
            self.current_session.end_time - self.current_session.start_time
        ).total_seconds() * 1000
        
        self.current_session.success = success
        self.current_session.error_message = error_message
        
        # Calculate overall metrics
        self._calculate_overall_metrics()
        
        # Generate performance summary
        self._generate_performance_summary()
        
        session = self.current_session
        self.current_session = None  # Reset for next session
        
        self.logger.info(
            f"Finalized session {session.session_id}: "
            f"{session.overall_extraction_rate:.1%} extraction, "
            f"{session.overall_confidence_score:.2f} confidence, "
            f"{session.total_processing_time_ms:.1f}ms"
        )
        
        return session
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Get extraction summary for current or last session"""
        if not self.current_session:
            return {}
        
        session = self.current_session
        
        # Calculate total fields
        total_fields = sum(
            metrics.fields_attempted 
            for metrics in session.component_metrics.values()
        )
        extracted_fields = sum(
            metrics.fields_extracted 
            for metrics in session.component_metrics.values()
        )
        
        return {
            'total_possible_fields': total_fields,
            'extracted_fields': extracted_fields,
            'extraction_rate': (extracted_fields / max(total_fields, 1)) * 100,
            'confidence_score': session.overall_confidence_score,
            'processing_time_seconds': session.total_processing_time_ms / 1000,
            'validation_score': session.validation_summary.get('confidence_score', 0.0),
            'tables_processed': len(session.table_metrics),
            'success': session.success
        }
    
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics for current session"""
        if not self.current_session:
            return {}
        
        session = self.current_session
        
        return {
            'session_info': {
                'session_id': session.session_id,
                'file_name': session.file_name,
                'processing_time_ms': session.total_processing_time_ms,
                'success': session.success
            },
            'component_breakdown': {
                component.value: {
                    'extraction_rate': metrics.extraction_rate,
                    'confidence_score': metrics.confidence_score,
                    'processing_time_ms': metrics.processing_time_ms,
                    'fields_extracted': f"{metrics.fields_extracted}/{metrics.fields_attempted}",
                    'validation_issues': metrics.validation_issues,
                    'tables_utilized': f"{metrics.tables_utilized}/{metrics.tables_processed}"
                }
                for component, metrics in session.component_metrics.items()
            },
            'table_analysis': [
                {
                    'index': table.table_index,
                    'type': table.table_type,
                    'dimensions': f"{table.rows}x{table.cols}",
                    'utilization_rate': table.utilization_rate,
                    'relevance_score': table.relevance_score,
                    'extractors_used': table.extractors_used
                }
                for table in session.table_metrics
            ],
            'validation_summary': session.validation_summary,
            'performance_summary': session.performance_summary
        }
    
    def _count_extracted_fields(self, extraction_result: Any, expected_fields: List[str]) -> int:
        """Count successfully extracted fields"""
        if not extraction_result:
            return 0
        
        extracted_count = 0
        for field_name in expected_fields:
            value = getattr(extraction_result, field_name, None)
            if value is not None and value != '' and value != 0:
                extracted_count += 1
        
        return extracted_count
    
    def _calculate_component_confidence(
        self, 
        extraction_result: Any, 
        validation_issues: int, 
        fields_extracted: int, 
        fields_attempted: int
    ) -> float:
        """Calculate confidence score for a component"""
        if fields_attempted == 0:
            return 1.0
        
        # Base confidence from extraction rate
        extraction_rate = fields_extracted / fields_attempted
        base_confidence = extraction_rate
        
        # Penalty for validation issues
        validation_penalty = min(validation_issues * 0.1, 0.5)
        
        # Adjust for field quality (non-empty, reasonable values)
        quality_bonus = self._assess_field_quality(extraction_result) * 0.2
        
        final_confidence = max(0.0, min(1.0, base_confidence - validation_penalty + quality_bonus))
        return final_confidence
    
    def _assess_field_quality(self, extraction_result: Any) -> float:
        """Assess the quality of extracted fields"""
        if not extraction_result:
            return 0.0
        
        # Simple heuristic: check for reasonable field values
        quality_indicators = 0
        total_checks = 0
        
        # Check string fields are not empty or placeholder
        string_fields = ['name', 'address', 'designation']
        for field in string_fields:
            value = getattr(extraction_result, field, None)
            total_checks += 1
            if value and len(str(value).strip()) > 2 and 'not found' not in str(value).lower():
                quality_indicators += 1
        
        # Check numeric fields are reasonable
        numeric_fields = ['basic_salary', 'gross_salary', 'total_income']
        for field in numeric_fields:
            value = getattr(extraction_result, field, None)
            total_checks += 1
            if value and float(value) > 0 and float(value) < 100000000:  # Reasonable salary range
                quality_indicators += 1
        
        return quality_indicators / max(total_checks, 1)
    
    def _calculate_overall_metrics(self):
        """Calculate overall session metrics"""
        session = self.current_session
        if not session.component_metrics:
            return
        
        # Overall extraction rate (weighted by fields)
        total_fields = sum(m.fields_attempted for m in session.component_metrics.values())
        extracted_fields = sum(m.fields_extracted for m in session.component_metrics.values())
        session.overall_extraction_rate = extracted_fields / max(total_fields, 1)
        
        # Overall confidence (weighted by component importance)
        component_weights = {
            ExtractorComponent.SALARY_EXTRACTOR: 0.3,
            ExtractorComponent.DEDUCTIONS_EXTRACTOR: 0.25,
            ExtractorComponent.TAX_EXTRACTOR: 0.2,
            ExtractorComponent.EMPLOYEE_EXTRACTOR: 0.1,
            ExtractorComponent.EMPLOYER_EXTRACTOR: 0.1,
            ExtractorComponent.METADATA_EXTRACTOR: 0.05
        }
        
        weighted_confidence = 0.0
        total_weight = 0.0
        
        for component, metrics in session.component_metrics.items():
            weight = component_weights.get(component, 0.1)
            weighted_confidence += metrics.confidence_score * weight
            total_weight += weight
        
        session.overall_confidence_score = weighted_confidence / max(total_weight, 1)
    
    def _generate_performance_summary(self):
        """Generate performance analysis summary"""
        session = self.current_session
        
        # Component performance analysis
        component_times = [m.processing_time_ms for m in session.component_metrics.values()]
        table_times = [t.processing_time_ms for t in session.table_metrics]
        
        session.performance_summary = {
            'total_time_ms': session.total_processing_time_ms,
            'component_time_ms': sum(component_times),
            'table_processing_time_ms': sum(table_times),
            'overhead_time_ms': session.total_processing_time_ms - sum(component_times),
            'avg_component_time_ms': statistics.mean(component_times) if component_times else 0,
            'slowest_component': max(
                session.component_metrics.items(), 
                key=lambda x: x[1].processing_time_ms
            )[0].value if session.component_metrics else None,
            'table_utilization': {
                'total_tables': len(session.table_metrics),
                'avg_utilization_rate': statistics.mean([t.utilization_rate for t in session.table_metrics]) if session.table_metrics else 0,
                'underutilized_tables': sum(1 for t in session.table_metrics if t.utilization_rate < 0.2)
            }
        }