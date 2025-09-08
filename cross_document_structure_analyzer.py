#!/usr/bin/env python3
"""
Cross-Document Structure Analysis
=================================

Compare table structures across different Form16 documents to:
1. Identify structural patterns and variations
2. Find document-specific anomalies  
3. Improve classification by understanding inter-document consistency
4. Create document-type-aware classification strategies
"""

import pickle
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict, Counter
import numpy as np
from dataclasses import dataclass

@dataclass
class TableStructure:
    """Standardized table structure representation"""
    shape: Tuple[int, int]
    classification: str
    confidence: float
    semantic_terms: int
    empty_ratio: float
    has_amounts: bool
    document: str
    table_index: int
    sample_headers: List[str]
    sample_content: List[str]

def load_extracted_data() -> List[Dict[str, Any]]:
    """Load our 138-table dataset"""
    pickle_file = Path("extracted_tables/focused_form16_tables.pkl")
    
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)
    
    print(f"Loaded {len(data)} documents with {sum(doc['total_tables'] for doc in data)} tables")
    return data

def extract_table_structures(data: List[Dict[str, Any]]) -> List[TableStructure]:
    """Convert raw data to standardized table structures"""
    
    structures = []
    
    for doc in data:
        doc_name = doc['document']
        
        for table in doc['tables']:
            # Extract sample content for comparison
            sample_df = pd.DataFrame(table.get('sample_data', []))
            
            sample_headers = []
            sample_content = []
            
            if not sample_df.empty:
                # Get meaningful headers
                sample_headers = [str(col) for col in sample_df.columns if str(col) not in ['0', '1', '2', '3', '4', '5']][:5]
                
                # Get meaningful content (non-empty, non-numeric, short strings)
                for row_idx in range(min(3, len(sample_df))):
                    for col in sample_df.columns:
                        cell_value = str(sample_df.iloc[row_idx][col]).strip()
                        if (cell_value and 
                            cell_value.lower() not in ['nan', 'none', ''] and
                            not cell_value.isdigit() and
                            len(cell_value) > 3 and 
                            len(cell_value) < 50):
                            sample_content.append(cell_value.lower())
                
                sample_content = sample_content[:10]  # Limit sample size
            
            structure = TableStructure(
                shape=tuple(table['shape']),
                classification=table['classification']['type'],
                confidence=table['classification']['confidence'],
                semantic_terms=table['structure'].get('form16_terms_found', 0),
                empty_ratio=table['structure'].get('empty_ratio', 0),
                has_amounts=len(table['structure'].get('amount_columns', [])) > 0,
                document=doc_name,
                table_index=table['index'],
                sample_headers=sample_headers,
                sample_content=sample_content
            )
            
            structures.append(structure)
    
    return structures

def analyze_cross_document_patterns(structures: List[TableStructure]) -> Dict[str, Any]:
    """Analyze patterns across different documents"""
    
    print(f"\nCROSS-DOCUMENT STRUCTURE ANALYSIS")
    print("=" * 70)
    
    analysis = {
        'document_signatures': {},
        'table_type_consistency': {},
        'structural_anomalies': [],
        'document_clusters': {},
        'classification_improvement_targets': []
    }
    
    # Group by document
    by_document = defaultdict(list)
    for structure in structures:
        by_document[structure.document].append(structure)
    
    documents = list(by_document.keys())
    print(f"Analyzing {len(documents)} documents:")
    for doc in documents:
        print(f"  {doc}: {len(by_document[doc])} tables")
    
    # 1. Create document signatures (table type sequences)
    print(f"\n📋 Document Signatures Analysis:")
    
    for doc_name, doc_structures in by_document.items():
        # Sort tables by index to get sequence
        sorted_tables = sorted(doc_structures, key=lambda x: x.table_index)
        
        # Create signature: sequence of table types
        type_sequence = [t.classification for t in sorted_tables]
        shape_sequence = [t.shape for t in sorted_tables]
        
        analysis['document_signatures'][doc_name] = {
            'type_sequence': type_sequence,
            'shape_sequence': shape_sequence,
            'total_tables': len(sorted_tables),
            'unique_types': len(set(type_sequence)),
            'avg_confidence': np.mean([t.confidence for t in sorted_tables])
        }
        
        print(f"  {doc_name}:")
        print(f"    Types: {' → '.join(type_sequence[:5])}{'...' if len(type_sequence) > 5 else ''}")
        print(f"    Avg confidence: {analysis['document_signatures'][doc_name]['avg_confidence']:.2f}")
    
    # 2. Table type consistency analysis
    print(f"\nTable Type Consistency Analysis:")
    
    by_table_type = defaultdict(lambda: defaultdict(list))
    
    for structure in structures:
        by_table_type[structure.classification][structure.document].append(structure)
    
    for table_type in ['part_b_salary_details', 'part_b_tax_deductions', 'part_b_employer_employee']:
        if table_type not in by_table_type:
            continue
            
        print(f"\n  {table_type}:")
        type_analysis = {}
        
        doc_shapes = {}
        doc_confidences = {}
        doc_contents = {}
        
        for doc_name, doc_tables in by_table_type[table_type].items():
            shapes = [t.shape for t in doc_tables]
            confidences = [t.confidence for t in doc_tables]
            contents = []
            
            # Collect content samples
            for table in doc_tables:
                contents.extend(table.sample_content)
            
            doc_shapes[doc_name] = shapes
            doc_confidences[doc_name] = confidences
            doc_contents[doc_name] = list(set(contents))  # Unique content
            
            print(f"    {doc_name}: shapes={shapes}, conf={np.mean(confidences):.2f}")
        
        # Find structural variations
        all_shapes = []
        for shapes_list in doc_shapes.values():
            all_shapes.extend(shapes_list)
        
        shape_variations = len(set(all_shapes))
        most_common_shapes = Counter(all_shapes).most_common(3)
        
        type_analysis = {
            'documents_with_type': len(doc_shapes),
            'total_instances': len(all_shapes),
            'shape_variations': shape_variations,
            'common_shapes': most_common_shapes,
            'avg_confidence_by_doc': {doc: np.mean(confs) for doc, confs in doc_confidences.items()},
            'content_overlap': analyze_content_overlap(doc_contents)
        }
        
        analysis['table_type_consistency'][table_type] = type_analysis
        
        print(f"    Shape variations: {shape_variations}")
        print(f"    Most common: {most_common_shapes}")
        print(f"    Content overlap: {type_analysis['content_overlap']:.1%}")
    
    # 3. Structural anomaly detection
    print(f"\nStructural Anomaly Detection:")
    
    anomalies = find_structural_anomalies(by_document, by_table_type)
    analysis['structural_anomalies'] = anomalies
    
    for anomaly in anomalies:
        print(f"    {anomaly['type']}: {anomaly['description']}")
    
    # 4. Document clustering based on structure
    print(f"\n🔗 Document Clustering Analysis:")
    
    clusters = cluster_documents_by_structure(analysis['document_signatures'])
    analysis['document_clusters'] = clusters
    
    for cluster_id, cluster_docs in clusters.items():
        print(f"    Cluster {cluster_id}: {cluster_docs}")
    
    # 5. Classification improvement targets
    print(f"\nClassification Improvement Targets:")
    
    improvement_targets = identify_improvement_targets(structures, analysis)
    analysis['classification_improvement_targets'] = improvement_targets
    
    for target in improvement_targets:
        print(f"    {target}")
    
    return analysis

def analyze_content_overlap(doc_contents: Dict[str, List[str]]) -> float:
    """Calculate content overlap between documents for same table type"""
    
    if len(doc_contents) < 2:
        return 0.0
    
    # Find intersection of all document contents
    doc_sets = [set(contents) for contents in doc_contents.values()]
    
    if not doc_sets:
        return 0.0
    
    # Calculate Jaccard similarity (intersection / union)
    intersection = set.intersection(*doc_sets)
    union = set.union(*doc_sets)
    
    return len(intersection) / len(union) if union else 0.0

def find_structural_anomalies(by_document: Dict[str, List[TableStructure]], 
                             by_table_type: Dict[str, Dict[str, List[TableStructure]]]) -> List[Dict[str, Any]]:
    """Detect structural anomalies across documents"""
    
    anomalies = []
    
    # 1. Documents with unusual table counts
    table_counts = [len(tables) for tables in by_document.values()]
    mean_count = np.mean(table_counts)
    std_count = np.std(table_counts)
    
    for doc_name, tables in by_document.items():
        if abs(len(tables) - mean_count) > 2 * std_count:
            anomalies.append({
                'type': 'unusual_table_count',
                'document': doc_name,
                'description': f"{doc_name} has {len(tables)} tables (avg: {mean_count:.1f})"
            })
    
    # 2. Table types that appear in some documents but not others
    for table_type, doc_tables in by_table_type.items():
        total_docs = len(by_document)
        docs_with_type = len(doc_tables)
        
        if docs_with_type < total_docs * 0.5 and docs_with_type > 1:  # Missing from >50% but exists
            missing_docs = set(by_document.keys()) - set(doc_tables.keys())
            anomalies.append({
                'type': 'missing_table_type',
                'table_type': table_type,
                'description': f"{table_type} missing from {len(missing_docs)} documents: {list(missing_docs)}"
            })
    
    # 3. Confidence anomalies (tables with unusually low/high confidence for their type)
    for table_type, doc_tables in by_table_type.items():
        if len(doc_tables) < 2:
            continue
            
        all_confidences = []
        for tables in doc_tables.values():
            all_confidences.extend([t.confidence for t in tables])
        
        if all_confidences:
            mean_conf = np.mean(all_confidences)
            std_conf = np.std(all_confidences)
            
            for doc_name, tables in doc_tables.items():
                for table in tables:
                    if abs(table.confidence - mean_conf) > 2 * std_conf:
                        anomalies.append({
                            'type': 'confidence_anomaly',
                            'document': doc_name,
                            'table_type': table_type,
                            'description': f"{doc_name} {table_type} confidence {table.confidence:.2f} (avg: {mean_conf:.2f})"
                        })
    
    return anomalies

def cluster_documents_by_structure(document_signatures: Dict[str, Dict[str, Any]]) -> Dict[int, List[str]]:
    """Cluster documents based on structural similarity"""
    
    # Simple clustering based on table type sequences
    sequence_groups = defaultdict(list)
    
    for doc_name, signature in document_signatures.items():
        # Create a simplified signature for clustering
        type_counts = Counter(signature['type_sequence'])
        
        # Create a hashable representation
        signature_key = tuple(sorted(type_counts.items()))
        sequence_groups[signature_key].append(doc_name)
    
    # Convert to numbered clusters
    clusters = {}
    for cluster_id, (signature_key, docs) in enumerate(sequence_groups.items()):
        if len(docs) > 1:  # Only keep clusters with multiple documents
            clusters[cluster_id] = docs
    
    return clusters

def identify_improvement_targets(structures: List[TableStructure], 
                                analysis: Dict[str, Any]) -> List[str]:
    """Identify specific targets for classification improvement"""
    
    targets = []
    
    # 1. Low confidence tables that appear consistently across documents
    low_conf_by_type = defaultdict(list)
    
    for structure in structures:
        if structure.confidence < 0.6:
            low_conf_by_type[structure.classification].append(structure)
    
    for table_type, low_conf_tables in low_conf_by_type.items():
        if len(low_conf_tables) >= 3:  # Appears in multiple documents
            docs_affected = len(set(t.document for t in low_conf_tables))
            targets.append(f"Improve {table_type} classification (low confidence in {docs_affected} documents)")
    
    # 2. High shape variation types
    for table_type, type_analysis in analysis['table_type_consistency'].items():
        if type_analysis['shape_variations'] > 3:
            targets.append(f"Add shape tolerance for {table_type} ({type_analysis['shape_variations']} variations)")
    
    # 3. Content-based improvements for low overlap types
    for table_type, type_analysis in analysis['table_type_consistency'].items():
        if type_analysis['content_overlap'] < 0.3:
            targets.append(f"Improve content-based classification for {table_type} (low content overlap)")
    
    return targets

def generate_classification_improvements(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate specific classification improvements based on cross-document analysis"""
    
    print(f"\n🚀 CLASSIFICATION IMPROVEMENT RECOMMENDATIONS")
    print("=" * 70)
    
    improvements = {
        'pattern_updates': {},
        'confidence_adjustments': {},
        'document_specific_rules': {},
        'shape_tolerance_updates': {}
    }
    
    # 1. Pattern updates based on consistent content
    print(f"\n📝 Pattern Updates:")
    
    for table_type, type_analysis in analysis['table_type_consistency'].items():
        print(f"\n  {table_type}:")
        
        # Shape patterns update
        common_shapes = [shape for shape, count in type_analysis['common_shapes']]
        improvements['shape_tolerance_updates'][table_type] = common_shapes
        print(f"    Update shape patterns: {common_shapes}")
        
        # Confidence adjustments
        avg_confidences = type_analysis['avg_confidence_by_doc']
        low_conf_docs = [doc for doc, conf in avg_confidences.items() if conf < 0.7]
        
        if low_conf_docs:
            improvements['confidence_adjustments'][table_type] = {
                'boost_needed': True,
                'affected_documents': low_conf_docs,
                'suggested_boost': 0.15
            }
            print(f"    Confidence boost needed for: {low_conf_docs}")
    
    # 2. Document-specific rules
    print(f"\n📄 Document-Specific Rules:")
    
    for cluster_id, cluster_docs in analysis['document_clusters'].items():
        if len(cluster_docs) > 1:
            print(f"    Cluster {cluster_id} documents have similar structure: {cluster_docs}")
            improvements['document_specific_rules'][f'cluster_{cluster_id}'] = {
                'documents': cluster_docs,
                'rule': 'Apply cluster-specific classification patterns'
            }
    
    # 3. Anomaly-based improvements
    print(f"\nAnomaly-Based Improvements:")
    
    for anomaly in analysis['structural_anomalies']:
        if anomaly['type'] == 'confidence_anomaly':
            print(f"    Fix confidence calculation for {anomaly.get('table_type', 'unknown')} in {anomaly.get('document', 'unknown')}")
        elif anomaly['type'] == 'missing_table_type':
            print(f"    Review classification patterns for {anomaly.get('table_type', 'unknown')}")
    
    return improvements

def main():
    """Run cross-document structure analysis"""
    
    print("🔬 Cross-Document Form16 Structure Analysis")
    print("=" * 80)
    
    # Load data
    data = load_extracted_data()
    if not data:
        print("No data available")
        return
    
    # Extract standardized structures
    structures = extract_table_structures(data)
    print(f"Extracted {len(structures)} table structures for analysis")
    
    # Run cross-document analysis
    analysis = analyze_cross_document_patterns(structures)
    
    # Generate improvement recommendations
    improvements = generate_classification_improvements(analysis)
    
    # Save results
    results = {
        'structures': [s.__dict__ for s in structures],  # Convert dataclass to dict
        'cross_document_analysis': analysis,
        'improvement_recommendations': improvements,
        'summary': {
            'total_structures_analyzed': len(structures),
            'documents_analyzed': len(set(s.document for s in structures)),
            'anomalies_found': len(analysis['structural_anomalies']),
            'improvement_targets': len(analysis['classification_improvement_targets']),
            'document_clusters': len(analysis['document_clusters'])
        }
    }
    
    output_file = Path("extracted_tables/cross_document_analysis_results.pkl")
    with open(output_file, 'wb') as f:
        pickle.dump(results, f)
    
    print(f"\n💾 Analysis results saved to: {output_file}")
    
    # Summary
    print(f"\nANALYSIS SUMMARY:")
    print(f"Structures analyzed: {len(structures)}")
    print(f"Documents: {len(set(s.document for s in structures))}")
    print(f"Anomalies found: {len(analysis['structural_anomalies'])}")
    print(f"Improvement targets: {len(analysis['classification_improvement_targets'])}")
    
    print(f"\nCross-document analysis complete!")
    
    return results

if __name__ == "__main__":
    main()