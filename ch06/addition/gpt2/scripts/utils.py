#!/usr/bin/env python3
"""
Utility Functions for GPT-2 Math Fine-Tuning

This module contains helper functions used across multiple scripts.
"""

import json
import os
from pathlib import Path


def ensure_dir(directory):
    """
    Ensure a directory exists, create if it doesn't.
    
    Args:
        directory (str): Directory path
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def load_json(filepath):
    """
    Load data from a JSON file.
    
    Args:
        filepath (str): Path to JSON file
        
    Returns:
        dict or list: Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, filepath, indent=2):
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filepath (str): Output file path
        indent (int): JSON indentation
    """
    ensure_dir(os.path.dirname(filepath))
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def format_percentage(value):
    """
    Format a decimal as a percentage string.
    
    Args:
        value (float): Decimal value (0-1)
        
    Returns:
        str: Formatted percentage
    """
    return f"{value:.2%}"


def calculate_accuracy(correct, total):
    """
    Calculate accuracy percentage.
    
    Args:
        correct (int): Number of correct predictions
        total (int): Total number of predictions
        
    Returns:
        float: Accuracy (0-1)
    """
    return correct / total if total > 0 else 0.0


def print_section_header(title, width=60):
    """
    Print a formatted section header.
    
    Args:
        title (str): Section title
        width (int): Header width
    """
    print(f"\n{'='*width}")
    print(title)
    print('='*width)


def print_divider(width=60):
    """
    Print a divider line.
    
    Args:
        width (int): Divider width
    """
    print('-' * width)


class ProgressTracker:
    """Simple progress tracker for long-running operations."""
    
    def __init__(self, total, description="Processing"):
        self.total = total
        self.current = 0
        self.description = description
    
    def update(self, n=1):
        """Update progress by n steps."""
        self.current += n
        if self.current % max(1, self.total // 10) == 0:
            percentage = (self.current / self.total) * 100
            print(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)")
    
    def finish(self):
        """Mark progress as complete."""
        print(f"✓ {self.description}: {self.total}/{self.total} (100%)")


def get_operation_from_text(text):
    """
    Extract operation type from problem text.
    
    Args:
        text (str): Problem text
        
    Returns:
        str: Operation symbol (+, -, *, /) or None
    """
    for op in ['+', '-', '*', '/']:
        if op in text:
            return op
    return None


def validate_file_exists(filepath, file_description="File"):
    """
    Check if a file exists and raise error if not.
    
    Args:
        filepath (str): Path to file
        file_description (str): Description for error message
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"{file_description} not found: {filepath}\n"
            f"Please ensure you've run the previous steps in the pipeline."
        )


def get_project_root():
    """
    Get the project root directory.
    
    Returns:
        Path: Project root path
    """
    return Path(__file__).parent.parent


def get_data_dir():
    """Get the data directory path."""
    return get_project_root() / "data"


def get_results_dir():
    """Get the results directory path."""
    return get_project_root() / "results"


def get_model_dir():
    """Get the fine-tuned model directory path."""
    return get_project_root() / "fine_tuned_model"
