#!/usr/bin/env python3
"""
PAM 7 ASCII Format Verifier
Checks PAM files for format compliance and reports detailed information
"""

import sys
import os
from typing import Dict, List, Tuple, Optional

class PAMVerifier:
    def __init__(self):
        self.required_fields = {'WIDTH', 'HEIGHT', 'DEPTH', 'MAXVAL'}
        self.valid_tuple_types = {
            1: ['GRAYSCALE', 'BLACKANDWHITE'],
            2: ['GRAYSCALE_ALPHA'],
            3: ['RGB'],
            4: ['RGB_ALPHA']
        }
    
    def verify_file(self, filepath: str) -> Dict:
        """Verify a PAM file and return detailed results"""
        results = {
            'file': filepath,
            'valid': False,
            'errors': [],
            'warnings': [],
            'info': {},
            'header': {},
            'data_info': {}
        }
        
        try:
            if not os.path.exists(filepath):
                results['errors'].append(f"File does not exist: {filepath}")
                return results
            
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Check if it's ASCII
            try:
                text_content = content.decode('ascii')
            except UnicodeDecodeError:
                results['errors'].append("File is not ASCII encoded")
                return results
            
            # Split into lines
            lines = text_content.split('\n')
            
            # Verify magic number
            if not lines or not lines[0].strip() == 'P7':
                results['errors'].append("Invalid magic number - should be 'P7'")
                return results
            
            results['info']['magic_number'] = 'P7'
            
            # Parse header
            header_end_idx = self._parse_header(lines, results)
            if header_end_idx == -1:
                return results
            
            # Verify required fields
            self._verify_header_fields(results)
            if results['errors']:
                return results
            
            # Parse and verify data
            self._verify_data_section(lines, header_end_idx + 1, results)
            
            if not results['errors']:
                results['valid'] = True
                
        except Exception as e:
            results['errors'].append(f"Unexpected error: {str(e)}")
        
        return results
    
    def _parse_header(self, lines: List[str], results: Dict) -> int:
        """Parse PAM header and return index of ENDHDR line"""
        header_end_idx = -1
        current_line = 1  # Skip P7 line
        
        while current_line < len(lines):
            line = lines[current_line].strip()
            
            if line == 'ENDHDR':
                header_end_idx = current_line
                break
            
            if line == '' or line.startswith('#'):
                current_line += 1
                continue
            
            # Parse header field
            parts = line.split()
            if len(parts) >= 2:
                field_name = parts[0]
                field_value = parts[1]
                
                if field_name in ['WIDTH', 'HEIGHT', 'DEPTH', 'MAXVAL']:
                    try:
                        results['header'][field_name] = int(field_value)
                    except ValueError:
                        results['errors'].append(f"Invalid {field_name}: '{field_value}' is not an integer")
                elif field_name == 'TUPLTYPE':
                    results['header'][field_name] = field_value
                else:
                    results['warnings'].append(f"Unknown header field: {field_name}")
            else:
                results['warnings'].append(f"Malformed header line: '{line}'")
            
            current_line += 1
        
        if header_end_idx == -1:
            results['errors'].append("ENDHDR not found in header")
        
        return header_end_idx
    
    def _verify_header_fields(self, results: Dict):
        """Verify required header fields are present and valid"""
        header = results['header']
        
        # Check required fields
        for field in self.required_fields:
            if field not in header:
                results['errors'].append(f"Missing required field: {field}")
        
        if results['errors']:
            return
        
        # Validate field values
        width = header['WIDTH']
        height = header['HEIGHT']
        depth = header['DEPTH']
        maxval = header['MAXVAL']
        
        if width <= 0:
            results['errors'].append(f"WIDTH must be positive, got {width}")
        if height <= 0:
            results['errors'].append(f"HEIGHT must be positive, got {height}")
        if depth <= 0:
            results['errors'].append(f"DEPTH must be positive, got {depth}")
        if maxval <= 0 or maxval > 65535:
            results['errors'].append(f"MAXVAL must be 1-65535, got {maxval}")
        
        # Check TUPLTYPE if present
        if 'TUPLTYPE' in header:
            tupltype = header['TUPLTYPE']
            if depth in self.valid_tuple_types:
                if tupltype not in self.valid_tuple_types[depth]:
                    results['warnings'].append(
                        f"TUPLTYPE '{tupltype}' unusual for DEPTH {depth}. "
                        f"Expected one of: {self.valid_tuple_types[depth]}"
                    )
        else:
            results['warnings'].append("TUPLTYPE not specified")
    
    def _verify_data_section(self, lines: List[str], data_start_idx: int, results: Dict):
        """Verify the data section contains correct number of values"""
        header = results['header']
        
        if results['errors']:
            return
        
        width = header['WIDTH']
        height = header['HEIGHT']
        depth = header['DEPTH']
        maxval = header['MAXVAL']
        
        expected_values = width * height * depth
        
        # Collect all data values
        data_values = []
        line_count = 0
        
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if line == '' or line.startswith('#'):
                continue
            
            line_count += 1
            parts = line.split()
            
            for part in parts:
                try:
                    value = int(part)
                    if value < 0 or value > maxval:
                        results['errors'].append(
                            f"Data value {value} out of range [0, {maxval}] at line {i+1}"
                        )
                    data_values.append(value)
                except ValueError:
                    results['errors'].append(f"Invalid data value '{part}' at line {i+1}")
        
        # Check count
        actual_values = len(data_values)
        results['data_info'] = {
            'expected_values': expected_values,
            'actual_values': actual_values,
            'data_lines': line_count,
            'pixels': width * height
        }
        
        if actual_values != expected_values:
            results['errors'].append(
                f"Data count mismatch: expected {expected_values} values, got {actual_values}"
            )
        
        # Sample some values for verification
        if data_values and not results['errors']:
            results['data_info']['sample_values'] = data_values[:min(20, len(data_values))]
            results['data_info']['value_range'] = f"[{min(data_values)}, {max(data_values)}]"

def print_results(results: Dict):
    """Print verification results in a readable format"""
    print(f"\n{'='*60}")
    print(f"PAM FILE VERIFICATION: {results['file']}")
    print(f"{'='*60}")
    
    if results['valid']:
        print("FILE IS VALID")
    else:
        print("FILE HAS ERRORS")
    
    # Header info
    if results['header']:
        print(f"\n📋 HEADER INFORMATION:")
        for field, value in results['header'].items():
            print(f"   {field}: {value}")
    
    # Data info
    if results['data_info']:
        print(f"\nDATA INFORMATION:")
        data = results['data_info']
        print(f"   Expected values: {data.get('expected_values', 'N/A')}")
        print(f"   Actual values: {data.get('actual_values', 'N/A')}")
        print(f"   Data lines: {data.get('data_lines', 'N/A')}")
        print(f"   Total pixels: {data.get('pixels', 'N/A')}")
        if 'value_range' in data:
            print(f"   Value range: {data['value_range']}")
        if 'sample_values' in data:
            print(f"   Sample values: {data['sample_values']}")
    
    # Errors
    if results['errors']:
        print(f"\nERRORS ({len(results['errors'])}):")
        for i, error in enumerate(results['errors'], 1):
            print(f"   {i}. {error}")
    
    # Warnings
    if results['warnings']:
        print(f"\nWARNINGS ({len(results['warnings'])}):")
        for i, warning in enumerate(results['warnings'], 1):
            print(f"   {i}. {warning}")
    
    print(f"\n{'='*60}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python pam_verifier.py <pam_file>")
        print("Example: python pam_verifier.py image.pam")
        sys.exit(1)
    
    filepath = sys.argv[1]
    verifier = PAMVerifier()
    results = verifier.verify_file(filepath)
    print_results(results)
    
    # Exit with error code if file is invalid
    sys.exit(0 if results['valid'] else 1)

if __name__ == "__main__":
    main()