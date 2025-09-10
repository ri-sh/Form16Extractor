"""
Unit tests for multi-company Form16 consolidator.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock

from form16_extractor.consolidators.multi_company_consolidator import (
    MultiCompanyForm16Consolidator, ConsolidationStatus, ConsolidatedSalaryData,
    ConsolidatedTDSData, ConsolidatedDeductionsData
)
from form16_extractor.utils.validation import ValidationError


class TestMultiCompanyForm16Consolidator:
    """Test cases for MultiCompanyForm16Consolidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.consolidator = MultiCompanyForm16Consolidator()
        
        # Create mock Form16 documents
        self.form16_1 = self._create_mock_form16(
            employer_name="Example Company A",
            employee_pan="TEST12345F",
            employee_name="Test Employee",
            gross_salary=2000000,
            tds_deducted=200000,
            section_80c=100000,
            section_80d=25000
        )
        
        self.form16_2 = self._create_mock_form16(
            employer_name="Example Company B", 
            employee_pan="TEST12345F",
            employee_name="Test Employee",
            gross_salary=1500000,
            tds_deducted=150000,
            section_80c=50000,
            section_80d=0
        )
    
    def _create_mock_form16(self, employer_name, employee_pan, employee_name,
                           gross_salary, tds_deducted, section_80c, section_80d):
        """Create a mock Form16 document."""
        form16 = Mock()
        
        # Mock Part A structure
        form16.part_a = Mock()
        form16.part_a.employer = Mock()
        form16.part_a.employer.name = employer_name
        
        form16.part_a.employee = Mock()
        form16.part_a.employee.pan = employee_pan
        form16.part_a.employee.name = employee_name
        
        # Mock financial year
        form16.part_a.financial_year = "2023-24"
        form16.part_a.assessment_year = "2024-25"
        
        # Mock quarterly TDS summary
        form16.part_a.quarterly_tds_summary = Mock()
        form16.part_a.quarterly_tds_summary.total_tds = Mock()
        form16.part_a.quarterly_tds_summary.total_tds.deducted = tds_deducted
        form16.part_a.quarterly_tds_summary.total_tds.deposited = tds_deducted
        
        # Mock quarterly data
        for i in range(1, 5):
            quarter = Mock()
            quarter.amount_paid_credited = gross_salary / 4  # Split equally
            quarter.amount_deducted = tds_deducted / 4
            quarter.amount_deposited = tds_deducted / 4
            quarter.receipt_numbers = [f"Q{i}123456"]
            setattr(form16.part_a.quarterly_tds_summary, f'quarter_{i}', quarter)
        
        # Mock Part B structure
        form16.part_b = Mock()
        form16.part_b.gross_salary = Mock()
        form16.part_b.gross_salary.section_17_1_salary = gross_salary * 0.8
        form16.part_b.gross_salary.section_17_2_perquisites = gross_salary * 0.2
        form16.part_b.gross_salary.section_17_3_profits_in_lieu = 0
        form16.part_b.gross_salary.total = gross_salary
        
        # Mock deductions
        form16.part_b.chapter_vi_a_deductions = Mock()
        
        # Section 80C
        section_80c_obj = Mock()
        section_80c_obj.deductible_amount = section_80c if section_80c > 0 else None
        section_80c_obj.components = Mock()
        form16.part_b.chapter_vi_a_deductions.section_80C = section_80c_obj
        
        # Section 80D
        section_80d_obj = Mock()
        section_80d_obj.deductible_amount = section_80d if section_80d > 0 else None
        form16.part_b.chapter_vi_a_deductions.section_80D = section_80d_obj
        
        # Section 80CCD(1B)
        section_80ccd_obj = Mock()
        section_80ccd_obj.deductible_amount = None
        form16.part_b.chapter_vi_a_deductions.section_80CCD_1B = section_80ccd_obj
        
        return form16
    
    def test_consolidate_form16s_success(self):
        """Test successful consolidation of multiple Form16s."""
        form16_list = [self.form16_1, self.form16_2]
        
        result = self.consolidator.consolidate_form16s(form16_list)
        
        assert result.status == ConsolidationStatus.SUCCESS
        assert result.employee_pan == "TEST12345F"
        assert result.form16_count == 2
        assert len(result.source_employers) == 2
        assert "Example Company A" in result.source_employers
        assert "Example Company B" in result.source_employers
    
    def test_consolidate_salary_data(self):
        """Test salary data consolidation."""
        form16_list = [self.form16_1, self.form16_2]
        
        result = self.consolidator.consolidate_form16s(form16_list)
        salary_data = result.salary_data
        
        # Total gross salary should be sum of both
        expected_total = Decimal('2000000') + Decimal('1500000')
        assert salary_data.total_gross_salary == expected_total
        
        # Should have employer-wise breakdown
        assert "Example Company A" in salary_data.employer_wise_salary
        assert "Example Company B" in salary_data.employer_wise_salary
        
        # Verify individual employer amounts
        assert salary_data.employer_wise_salary["Example Company A"]["total"] == Decimal('2000000')
        assert salary_data.employer_wise_salary["Example Company B"]["total"] == Decimal('1500000')
    
    def test_consolidate_tds_data(self):
        """Test TDS data consolidation."""
        form16_list = [self.form16_1, self.form16_2]
        
        result = self.consolidator.consolidate_form16s(form16_list)
        tds_data = result.tds_data
        
        # Total TDS should be sum of both
        expected_total = Decimal('200000') + Decimal('150000')
        assert tds_data.total_tds_deducted == expected_total
        assert tds_data.total_tds_deposited == expected_total
        
        # Should have employer-wise breakdown
        assert "Example Company A" in tds_data.employer_wise_tds
        assert "Example Company B" in tds_data.employer_wise_tds
        
        # Should collect all receipt numbers
        assert len(tds_data.all_receipt_numbers) == 8  # 4 quarters × 2 employers
    
    def test_consolidate_deductions_within_limits(self):
        """Test deduction consolidation within limits."""
        form16_list = [self.form16_1, self.form16_2]
        
        result = self.consolidator.consolidate_form16s(form16_list)
        deductions_data = result.deductions_data
        
        # Total 80C should be sum but capped at limit
        total_80c = Decimal('100000') + Decimal('50000')  # 150K total
        assert deductions_data.section_80c_total == total_80c  # Within 1.5L limit
        
        # Total 80D should be sum
        total_80d = Decimal('25000') + Decimal('0')
        assert deductions_data.section_80d_total == total_80d
        
        # Should have employer-wise tracking
        assert "Example Company A" in deductions_data.employer_wise_deductions
        assert "Example Company B" in deductions_data.employer_wise_deductions
    
    def test_consolidate_deductions_over_limits(self):
        """Test deduction consolidation over limits."""
        # Modify form16s to have excessive deductions
        self.form16_1.part_b.chapter_vi_a_deductions.section_80C.deductible_amount = 150000
        self.form16_2.part_b.chapter_vi_a_deductions.section_80C.deductible_amount = 100000
        
        form16_list = [self.form16_1, self.form16_2]
        
        result = self.consolidator.consolidate_form16s(form16_list)
        deductions_data = result.deductions_data
        
        # Should be capped at limit
        assert deductions_data.section_80c_total == Decimal('150000')  # 1.5L limit
        
        # Should have duplicate warnings
        assert len(deductions_data.potential_duplicates) > 0
        over_limit_duplicate = next(
            (d for d in deductions_data.potential_duplicates if d['type'] == 'over_limit'),
            None
        )
        assert over_limit_duplicate is not None
        assert over_limit_duplicate['claimed_amount'] == 250000  # Total claimed
        assert over_limit_duplicate['limit'] == 150000
    
    def test_validate_form16_consistency_success(self):
        """Test Form16 consistency validation - success case."""
        form16_list = [self.form16_1, self.form16_2]
        
        # Should not raise exception
        self.consolidator._validate_form16_consistency(form16_list)
    
    def test_validate_form16_consistency_pan_mismatch(self):
        """Test Form16 consistency validation - PAN mismatch."""
        # Change PAN in second form16
        self.form16_2.part_a.employee.pan = "TEST99999Z"
        
        form16_list = [self.form16_1, self.form16_2]
        
        with pytest.raises(ValidationError, match="PAN mismatch"):
            self.consolidator._validate_form16_consistency(form16_list)
    
    def test_validate_form16_consistency_name_mismatch(self):
        """Test Form16 consistency validation - name mismatch."""
        # Change name in second form16
        self.form16_2.part_a.employee.name = "Test Employee B"
        
        form16_list = [self.form16_1, self.form16_2]
        
        with pytest.raises(ValidationError, match="name mismatch"):
            self.consolidator._validate_form16_consistency(form16_list)
    
    def test_detect_duplicate_deductions(self):
        """Test duplicate deduction detection."""
        # Set same deduction amounts (potential duplicate)
        self.form16_1.part_b.chapter_vi_a_deductions.section_80C.deductible_amount = 100000
        self.form16_2.part_b.chapter_vi_a_deductions.section_80C.deductible_amount = 100000
        
        form16_list = [self.form16_1, self.form16_2]
        
        result = self.consolidator.consolidate_form16s(form16_list)
        deductions_data = result.deductions_data
        
        # Should detect duplicate amounts
        duplicate_amount_duplicate = next(
            (d for d in deductions_data.potential_duplicates if d['type'] == 'duplicate_amount'),
            None
        )
        assert duplicate_amount_duplicate is not None
        assert duplicate_amount_duplicate['amount'] == 100000
        assert len(duplicate_amount_duplicate['employers']) == 2
    
    def test_calculate_consolidation_confidence(self):
        """Test consolidation confidence calculation."""
        form16_list = [self.form16_1, self.form16_2]
        
        result = self.consolidator.consolidate_form16s(form16_list)
        
        # Should have reasonable confidence score
        assert 0.0 <= result.consolidation_confidence <= 1.0
        
        # With good data, should have high confidence
        assert result.consolidation_confidence >= 0.7
    
    def test_consolidate_single_form16_error(self):
        """Test error when consolidating single Form16."""
        with pytest.raises(ValidationError, match="No Form16 data provided"):
            self.consolidator.consolidate_form16s([])
    
    def test_financial_year_determination(self):
        """Test financial year determination."""
        form16_list = [self.form16_1, self.form16_2]
        
        result = self.consolidator.consolidate_form16s(form16_list)
        
        # Should have determined financial year
        assert result.financial_year == "2023-24"  # From mock data
        assert result.assessment_year == "2024-25"  # FY + 1
    
    def test_validation_warnings_generated(self):
        """Test that validation warnings are generated appropriately."""
        # Create scenario with high TDS ratio
        self.form16_1.part_a.quarterly_tds_summary.total_tds.deducted = 1500000  # Very high TDS (>35% of total salary)
        
        form16_list = [self.form16_1, self.form16_2]
        
        result = self.consolidator.consolidate_form16s(form16_list)
        
        # Should have warnings due to high TDS ratio
        assert len(result.warnings) > 0
        high_tds_warning = next(
            (w for w in result.warnings if w.type == "high_tds_ratio"),
            None
        )
        assert high_tds_warning is not None
    
    def test_names_match_function(self):
        """Test the name matching function."""
        # Should match with minor variations
        assert self.consolidator._names_match("Test Employee", "Test Employee") == True
        assert self.consolidator._names_match("Test Employee.", "Test Employee") == True
        assert self.consolidator._names_match("Test, Employee", "Test Employee") == True
        assert self.consolidator._names_match("test employee", "Test Employee") == True
        
        # Should not match different names
        assert self.consolidator._names_match("Test Employee", "Test Employee B") == False