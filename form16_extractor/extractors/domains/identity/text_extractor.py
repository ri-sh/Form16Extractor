"""
Text-based Identity Extraction
=============================

Handles text-based extraction patterns for identity information from PDF documents.
This module extracts data using colon-split patterns and other text-based methods.
"""

import logging
import re
from typing import Dict, Optional, Any, List
from pathlib import Path


class IdentityTextExtractor:
    """
    Text-based extractor for identity information from PDF documents.
    Handles patterns like "Employee Name : RISHABH ROY" that are found in PDF text.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize regex patterns for identity extraction with priority ordering"""
        return {
            # High priority patterns - employee declaration/certification sections
            'employee_name': re.compile(r'(?:Full\s+Name\s*:\s*([A-Z][A-Z\s]+)(?:\s+(?:Designation|EMPID|Page))|do\s+hereby\s+(?:declare|certify).*?Full\s+Name\s*:\s*([A-Z][A-Z\s]+))', re.IGNORECASE | re.DOTALL),
            'employee_pan': re.compile(r'(?:Employee|EMP)\s*PAN\s*[:\-]?\s*([A-Z]{5}[0-9]{4}[A-Z]{1})', re.IGNORECASE),
            'employee_address': re.compile(r'(?:Employee|EMP)\s*Address\s*[:\-]?\s*(.+?)(?:\n\n|\nPAN|\n[A-Z]{4})', re.IGNORECASE | re.DOTALL),
            'employer_name': re.compile(r'(?:Name\s+of\s+the\s+Employer|Employer\s+Name)\s*[:\-]?\s*(.+?)(?:\n|TAN)', re.IGNORECASE),
            'employer_tan': re.compile(r'TAN\s*[:\-]?\s*([A-Z]{4}[0-9]{5}[A-Z]{1})', re.IGNORECASE),
            'employer_pan': re.compile(r'(?:Employer|EMP)\s*PAN\s*[:\-]?\s*([A-Z]{5}[0-9]{4}[A-Z]{1})', re.IGNORECASE),
            'assessment_year': re.compile(r'Assessment\s+Year\s*[:\-]?\s*(\d{4}-\d{2})', re.IGNORECASE),
            'financial_year': re.compile(r'Financial\s+Year\s*[:\-]?\s*(\d{4}-\d{2})', re.IGNORECASE),
        }
    
    def extract_from_text(self, pdf_text: str) -> Dict[str, Any]:
        """
        Extract identity information from PDF text using pattern matching
        
        Args:
            pdf_text: Raw text extracted from PDF
            
        Returns:
            Dict containing extracted identity information
        """
        if not pdf_text:
            return {}
        
        self.logger.debug("Extracting identity information from PDF text")
        
        extracted_data = {}
        
        # Primary strategy: Line-by-line colon-split extraction
        line_by_line_data = self._extract_line_by_line_colon_split(pdf_text)
        extracted_data.update(line_by_line_data)
        
        # Secondary strategy: Regex patterns for complex cases
        for field_name, pattern in self._patterns.items():
            try:
                if field_name in extracted_data:
                    # Skip if already found via line-by-line method
                    continue
                    
                if field_name == 'employee_name':
                    # Special handling for employee name with multiple group support
                    matches = pattern.finditer(pdf_text)
                    best_match = self._find_best_employee_name_match(matches)
                    if best_match:
                        extracted_data[field_name] = best_match
                        self.logger.debug(f"Found {field_name}: {best_match}")
                else:
                    # Standard pattern matching for other fields
                    match = pattern.search(pdf_text)
                    if match:
                        # Handle multiple groups in the regex
                        value = None
                        for i in range(1, match.lastindex + 1 if match.lastindex else 2):
                            try:
                                group_value = match.group(i)
                                if group_value and group_value.strip() and group_value.strip() != 'None':
                                    value = group_value.strip()
                                    break
                            except:
                                continue
                        
                        if value:
                            extracted_data[field_name] = value
                            self.logger.debug(f"Found {field_name}: {value}")
                            
            except Exception as e:
                self.logger.warning(f"Error extracting {field_name}: {str(e)}")
        
        # Fallback strategy: Legacy colon-split patterns
        colon_split_data = self._extract_colon_split_patterns(pdf_text)
        
        # Merge results, prioritizing line-by-line then regex matches
        for key, value in colon_split_data.items():
            if key not in extracted_data and value:
                extracted_data[key] = value
        
        self.logger.info(f"Text extraction found {len(extracted_data)} identity fields")
        return extracted_data
    
    def _extract_colon_split_patterns(self, text: str) -> Dict[str, str]:
        """
        Extract data using colon-split patterns from PDF text
        
        Args:
            text: Raw PDF text content
            
        Returns:
            Dict with extracted field mappings
        """
        if not text:
            return {}
        
        results = {}
        
        # Common colon-separated patterns in Form 16
        colon_patterns = {
            'employee_name': ['Employee Name', 'Name of the Employee', 'Employee'],
            'employee_pan': ['Employee PAN', 'PAN of Employee'],
            'employee_address': ['Employee Address', 'Address of Employee'],
            'employer_name': ['Name of the Employer', 'Employer Name', 'Employer'],
            'employer_tan': ['TAN', 'TAN Number'],
            'employer_pan': ['Employer PAN', 'PAN of Employer'],
            'assessment_year': ['Assessment Year', 'A.Y.'],
            'financial_year': ['Financial Year', 'F.Y.'],
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' not in line:
                continue
            
            # Split on colon and clean up
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
            
            key_part = parts[0].strip()
            value_part = parts[1].strip()
            
            if not value_part or value_part.lower() in ['none', '', 'null']:
                continue
            
            # Match against our patterns
            for field_name, patterns in colon_patterns.items():
                for pattern in patterns:
                    if self._fuzzy_match(key_part, pattern):
                        if field_name not in results:  # Don't overwrite existing matches
                            results[field_name] = value_part
                            break
        
        return results
    
    def _fuzzy_match(self, text: str, pattern: str, threshold: float = 0.8) -> bool:
        """
        Check if text fuzzy matches pattern
        
        Args:
            text: Text to match
            pattern: Pattern to match against
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            True if match found
        """
        # Simple fuzzy matching - normalize and check similarity
        text_norm = text.lower().strip()
        pattern_norm = pattern.lower().strip()
        
        # Exact match
        if text_norm == pattern_norm:
            return True
        
        # Contains match
        if pattern_norm in text_norm or text_norm in pattern_norm:
            return True
        
        # Word overlap for multi-word patterns
        if ' ' in pattern_norm:
            pattern_words = set(pattern_norm.split())
            text_words = set(text_norm.split())
            
            # Check if most pattern words are in text
            overlap = len(pattern_words.intersection(text_words))
            if overlap / len(pattern_words) >= threshold:
                return True
        
        return False
    
    def _extract_line_by_line_colon_split(self, pdf_text: str) -> Dict[str, Any]:
        """
        Extract identity information by reading text line by line and using colon-split strategy.
        This is the primary extraction method as suggested by the user.
        
        Args:
            pdf_text: Raw PDF text content
            
        Returns:
            Dict with extracted identity information
        """
        if not pdf_text:
            return {}
        
        self.logger.debug("Starting line-by-line colon-split extraction")
        
        results = {}
        lines = pdf_text.split('\n')
        
        # Field patterns to look for (key patterns that indicate the field)
        field_patterns = {
            'employee_name': [
                'employee name',
                'name of the employee', 
                'full name',
                'emp name',
                'employee full name'
            ],
            'employee_pan': [
                'employee pan',
                'pan of employee',
                'emp pan',
                'employee permanent account number'
            ],
            'employee_address': [
                'employee address',
                'address of employee',
                'emp address',
                'employee residential address'
            ],
            'employer_name': [
                'name of the employer',
                'employer name',
                'name of employer',
                'company name'
            ],
            'employer_tan': [
                'tan',
                'tan number',
                'employer tan',
                'tax deduction account number'
            ],
            'employer_pan': [
                'employer pan',
                'pan of employer',
                'company pan'
            ],
            'assessment_year': [
                'assessment year',
                'a.y.',
                'ay',
                'assessment yr'
            ],
            'financial_year': [
                'financial year',
                'f.y.',
                'fy',
                'financial yr'
            ]
        }
        
        # Track context for employee name scoring
        context_window = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                # Keep track of context lines for employee name scoring
                context_window.append((i, line.lower()))
                if len(context_window) > 10:  # Keep last 10 lines for context
                    context_window.pop(0)
                continue
            
            # Handle multi-line key-value patterns where key is on one line and value on the next
            if ':' not in line:
                # Check if this line could be a key for next line's value
                line_lower = line.lower()
                for field_name, patterns in field_patterns.items():
                    if field_name in results:
                        continue  # Already found this field
                    
                    for pattern in patterns:
                        if self._line_matches_pattern(line_lower, pattern):
                            # Look for value in next line
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                if next_line == ':' and i + 2 < len(lines):
                                    # Pattern: Key line, colon line, value line
                                    value_line = lines[i + 2].strip()
                                elif next_line and next_line != ':':
                                    # Pattern: Key line, value line
                                    value_line = next_line
                                else:
                                    continue
                                
                                if value_line and value_line.lower() not in ['none', '', 'null', '-', 'n/a']:
                                    # Apply context scoring for employee name
                                    if field_name == 'employee_name':
                                        cleaned_value = self._clean_employee_name(value_line)
                                            
                                        if cleaned_value:
                                            # Calculate context score
                                            context_text = ' '.join([ctx_line for _, ctx_line in context_window[-5:]])
                                            context_score = self._calculate_name_priority_score(context_text, cleaned_value)
                                            
                                            # Only accept if context score is positive
                                            if context_score > 0:
                                                results[field_name] = cleaned_value
                                                self.logger.debug(f"Multi-line found {field_name}: {cleaned_value} (score: {context_score})")
                                            else:
                                                self.logger.debug(f"Multi-line rejected {field_name}: {cleaned_value} (low context score: {context_score})")
                                    else:
                                        # For other fields, use direct extraction
                                        cleaned_value = self._clean_field_value(field_name, value_line)
                                        if cleaned_value:
                                            results[field_name] = cleaned_value
                                            self.logger.debug(f"Multi-line found {field_name}: {cleaned_value}")
                                    break
                
                # Keep track of context lines for employee name scoring
                context_window.append((i, line.lower()))
                if len(context_window) > 10:
                    context_window.pop(0)
                continue
            
            # Handle single-line colon-separated patterns
            colon_pos = line.find(':')
            if colon_pos == -1:
                continue
                
            key_part = line[:colon_pos].strip()
            value_part = line[colon_pos + 1:].strip()
            
            # Skip if no value or invalid value
            if not value_part or value_part.lower() in ['none', '', 'null', '-', 'n/a']:
                continue
            
            key_lower = key_part.lower()
            
            # Match against our field patterns
            for field_name, patterns in field_patterns.items():
                if field_name in results:
                    continue  # Already found this field
                
                for pattern in patterns:
                    if self._line_matches_pattern(key_lower, pattern):
                        # Special handling for employee name with context scoring
                        if field_name == 'employee_name':
                            cleaned_value = self._clean_employee_name(value_part)
                                
                            if cleaned_value:
                                # Calculate context score for this line
                                context_text = ' '.join([ctx_line for _, ctx_line in context_window[-5:]])  # Last 5 lines
                                context_score = self._calculate_name_priority_score(context_text, cleaned_value)
                                
                                # Only accept if context score is positive (employee section)
                                if context_score > 0:
                                    results[field_name] = cleaned_value
                                    self.logger.debug(f"Line-by-line found {field_name}: {cleaned_value} (score: {context_score})")
                                else:
                                    self.logger.debug(f"Rejected {field_name}: {cleaned_value} (low context score: {context_score})")
                        else:
                            # For non-name fields, use direct extraction
                            cleaned_value = self._clean_field_value(field_name, value_part)
                            if cleaned_value:
                                results[field_name] = cleaned_value
                                self.logger.debug(f"Line-by-line found {field_name}: {cleaned_value}")
                        break
            
            # Update context window with current line
            context_window.append((i, line.lower()))
            if len(context_window) > 10:
                context_window.pop(0)
        
        self.logger.debug(f"Line-by-line extraction found {len(results)} fields: {list(results.keys())}")
        return results
    
    def _line_matches_pattern(self, line_text: str, pattern: str) -> bool:
        """
        Check if a line matches a field pattern using fuzzy matching
        
        Args:
            line_text: The text from the line (already lowercased)
            pattern: The pattern to match against (lowercased)
            
        Returns:
            True if the line matches the pattern
        """
        # For single-word patterns like "designation", be more strict
        # The pattern should be at the beginning or end, not in the middle
        if ' ' not in pattern:
            # Pattern should be at start or end of line, or be the whole line
            words = line_text.split()
            if pattern in words:
                # Check position - should be at beginning or end
                if (words[0] == pattern or 
                    (len(words) > 1 and words[-1] == pattern) or
                    line_text == pattern):
                    return True
            return False
        
        # For multi-word patterns, use word-based matching
        pattern_words = set(pattern.split())
        line_words = set(line_text.split())
        
        # Check if most pattern words are present
        overlap = len(pattern_words.intersection(line_words))
        return overlap / len(pattern_words) >= 0.7
    
    def _clean_field_value(self, field_name: str, value: str) -> Optional[str]:
        """
        Clean and validate a field value based on field type
        
        Args:
            field_name: Name of the field
            value: Raw value to clean
            
        Returns:
            Cleaned value or None if invalid
        """
        if not value or not value.strip():
            return None
        
        cleaned = value.strip()
        
        # Field-specific validation
        if field_name in ['employee_pan', 'employer_pan']:
            # Validate PAN format: 5 letters, 4 digits, 1 letter
            if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', cleaned.upper()):
                return cleaned.upper()
            return None
        elif field_name == 'employer_tan':
            # Validate TAN format: 4 letters, 5 digits, 1 letter
            if re.match(r'^[A-Z]{4}[0-9]{5}[A-Z]{1}$', cleaned.upper()):
                return cleaned.upper()
            return None
        elif field_name in ['assessment_year', 'financial_year']:
            # Validate year format: YYYY-YY
            if re.match(r'^\d{4}-\d{2}$', cleaned):
                return cleaned
            return None
        elif field_name in ['employee_address', 'employer_name']:
            # General text fields - basic length validation
            if len(cleaned) > 5 and len(cleaned) < 500:
                return cleaned
            return None
        
        return cleaned if len(cleaned) > 1 else None
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted data
        
        Args:
            data: Raw extracted data
            
        Returns:
            Cleaned and validated data
        """
        validated = {}
        
        for key, value in data.items():
            if not value or str(value).strip() == '':
                continue
            
            # Clean the value
            cleaned_value = str(value).strip()
            
            # Field-specific validation
            if key == 'employee_pan' or key == 'employer_pan':
                # Validate PAN format
                if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', cleaned_value):
                    validated[key] = cleaned_value
            elif key == 'employer_tan':
                # Validate TAN format
                if re.match(r'^[A-Z]{4}[0-9]{5}[A-Z]{1}$', cleaned_value):
                    validated[key] = cleaned_value
            elif key in ['assessment_year', 'financial_year']:
                # Validate year format
                if re.match(r'^\d{4}-\d{2}$', cleaned_value):
                    validated[key] = cleaned_value
            else:
                # General text fields - just clean up
                if len(cleaned_value) > 1:  # Avoid single characters
                    validated[key] = cleaned_value
        
        return validated
    
    def _find_best_employee_name_match(self, matches) -> Optional[str]:
        """
        Find the best employee name match from multiple regex matches,
        prioritizing employee declaration sections over signing officer sections
        """
        candidate_names = []
        
        for match in matches:
            # Get the matched name from any of the groups
            name = None
            for i in range(1, match.lastindex + 1 if match.lastindex else 2):
                try:
                    group_value = match.group(i)
                    if group_value and group_value.strip():
                        name = group_value.strip()
                        break
                except:
                    continue
            
            if not name:
                continue
                
            # Clean up the name
            name = self._clean_employee_name(name)
            if not name:
                continue
            
            # Get context around the match to determine priority
            start_pos = max(0, match.start() - 200)
            end_pos = min(len(match.string), match.end() + 200)
            context = match.string[start_pos:end_pos].lower()
            
            # Score the match based on context
            priority_score = self._calculate_name_priority_score(context, name)
            
            candidate_names.append((name, priority_score, context[:50]))
            
        if not candidate_names:
            return None
        
        # Sort by priority score (highest first) and return the best match
        candidate_names.sort(key=lambda x: x[1], reverse=True)
        
        # Only accept candidates with positive scores (employee sections)
        best_score = candidate_names[0][1]
        if best_score <= 0:
            self.logger.debug(f"All employee name candidates have negative scores, rejecting all")
            self.logger.debug(f"Best candidate: {candidate_names[0][0]} (score: {best_score})")
            return None
        
        best_name = candidate_names[0][0]
        
        self.logger.debug(f"Employee name candidates: {[(name, score) for name, score, _ in candidate_names]}")
        self.logger.debug(f"Selected best match: {best_name}")
        
        return best_name
    
    def _clean_employee_name(self, name: str) -> Optional[str]:
        """Clean and validate extracted employee name"""
        if not name:
            return None
            
        # Remove common noise patterns
        name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
        name = name.strip()
        
        # Remove trailing noise like "Designation", "EMPID", etc.
        name = re.sub(r'\s*(?:Designation|EMPID|Page|Notes?|Certificate).*$', '', name, flags=re.IGNORECASE)
        
        # Must be at least 2 words and reasonable length
        if len(name.split()) < 2 or len(name) < 5 or len(name) > 50:
            return None
            
        # Should only contain letters and spaces
        if not re.match(r'^[A-Za-z\s]+$', name):
            return None
            
        return name.upper()
    
    def _calculate_name_priority_score(self, context: str, name: str) -> float:
        """
        Calculate priority score for employee name based on context.
        Higher score = more likely to be correct employee name
        """
        score = 0.0
        
        # High priority contexts (employee declaration/certification sections)
        high_priority_patterns = [
            'do hereby declare',
            'do hereby certify', 
            'employee declaration',
            'form 12bb',
            'form 12ba',
            'page 2 of 2',  # Employee sections are often on page 2
            'form 12bb',
            'based on books of account',
        ]
        
        # Medium priority contexts  
        medium_priority_patterns = [
            'full name',
            'empid',
            'employee id',
            'certificate number',
        ]
        
        # Low priority contexts (signing officer/employer sections - heavily penalize)
        low_priority_patterns = [
            'working in the capacity',
            'son/daughter',
            'capacity of',
            'page 4 of 4',  # Signing officer sections often on last page
            'person responsible',
            'verification',
            'certify that',
            'has been deducted',
            'deposited to the credit',
            'sum of rs',  # Tax deduction statements
            'amount deducted',
            'person responsible for deduction',
        ]
        
        for pattern in high_priority_patterns:
            if pattern in context:
                score += 10.0
                
        for pattern in medium_priority_patterns:
            if pattern in context:
                score += 5.0
                
        for pattern in low_priority_patterns:
            if pattern in context:
                score -= 5.0  # Heavily penalize signing officer sections
        
        # Add position-based scoring (employee data typically appears later in document)
        # Look for indicators of document section
        if any(indicator in context for indicator in ['page 2', 'page 3', 'annexure', 'part b']):
            score += 3.0  # Employee sections often in later parts
        
        if any(indicator in context for indicator in ['page 1', 'page 4', 'part a']):
            score -= 2.0  # Signing officer sections often in early/final parts
            
        # Additional scoring for employee-specific contexts
        if 'employee' in context.lower():
            score += 2.0
            
        return score


def create_identity_text_extractor() -> IdentityTextExtractor:
    """Create an identity text extractor instance"""
    return IdentityTextExtractor()