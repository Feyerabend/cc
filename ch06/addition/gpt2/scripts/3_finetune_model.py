#!/usr/bin/env python3
"""
Script 3: Fine-Tune GPT-2 on Math Dataset

This script fine-tunes a pre-trained GPT-2 model on the mathematical reasoning
dataset using Hugging Face's Trainer API.

Usage:
    python 3_finetune_model.py [OPTIONS]

Output:
    fine_tuned_model/ - Directory containing the fine-tuned model
    logs/ - Training logs and tensorboard files
"""

import json
import argparse
import os
from pathlib import Path
import torch
from transformers import (
    GPT2LMHeadModel,
    GPT2Tokenizer,
    GPT2Config,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from datasets import Dataset


def load_data(train_path, test_path=None):
    """
    Load training and optional test data.
    
    Args:
        train_path (str): Path to training JSON file
        test_path (str): Path to test JSON file (optional)
        
    Returns:
        tuple: (train_dataset, test_dataset) or (train_dataset, None)
    """
    print(f"Loading training data from: {train_path}")
    with open(train_path, 'r', encoding='utf-8') as f:
        train_data = json.load(f)
    
    train_dataset = Dataset.from_list(train_data)
    print(f"✓ Loaded {len(train_dataset)} training samples")
    
    test_dataset = None
    if test_path and os.path.exists(test_path):
        print(f"Loading test data from: {test_path}")
        with open(test_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        test_dataset = Dataset.from_list(test_data)
        print(f"✓ Loaded {len(test_dataset)} test samples")
    
    return train_dataset, test_dataset


def tokenize_dataset(dataset, tokenizer, max_length=128):
    """
    Tokenize the dataset for training.
    
    Args:
        dataset: Hugging Face Dataset object
        tokenizer: GPT2 tokenizer
        max_length (int): Maximum sequence length
        
    Returns:
        Dataset: Tokenized dataset
    """
    def tokenize_function(examples):
        # Tokenize with padding and truncation
        result = tokenizer(
            examples['text'],
            padding='max_length',
            truncation=True,
            max_length=max_length,
            return_tensors=None
        )
        # For causal language modeling, labels are the same as input_ids
        result['labels'] = result['input_ids'].copy()
        return result
    
    print(f"\nTokenizing dataset...")
    tokenized = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names,
        desc="Tokenizing"
    )
    print(f"✓ Tokenization complete")
    
    return tokenized


def setup_model_and_tokenizer(model_name='gpt2'):
    """
    Load pre-trained GPT-2 model and tokenizer.
    
    Args:
        model_name (str): Model identifier from Hugging Face
        
    Returns:
        tuple: (model, tokenizer)
    """
    print(f"\n{'='*60}")
    print(f"Loading pre-trained model: {model_name}")
    print('='*60)
    
    # Load tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    
    # Set pad token (GPT-2 doesn't have one by default)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Load model
    model = GPT2LMHeadModel.from_pretrained(model_name)
    
    # Print model info
    num_params = sum(p.numel() for p in model.parameters())
    print(f"✓ Model loaded: {num_params:,} parameters")
    
    return model, tokenizer


def check_gpu_availability():
    """Check and display GPU availability."""
    if torch.cuda.is_available():
        print(f"\n✓ CUDA is available")
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        return True
    else:
        print(f"\n⚠ CUDA not available - training will use CPU")
        print(f"  Training will be significantly slower")
        return False


def create_training_args(args, use_gpu):
    """
    Create TrainingArguments for the Trainer.
    
    Args:
        args: Command line arguments
        use_gpu (bool): Whether GPU is available
        
    Returns:
        TrainingArguments: Configuration for training
    """
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        warmup_steps=args.warmup_steps,
        weight_decay=args.weight_decay,
        logging_dir=args.log_dir,
        logging_steps=50,
        save_steps=500,
        save_total_limit=2,
        eval_strategy="steps" if args.eval_steps else "no",
        eval_steps=args.eval_steps if args.eval_steps else None,
        load_best_model_at_end=True if args.eval_steps else False,
        metric_for_best_model="loss" if args.eval_steps else None,
        greater_is_better=False,
        save_strategy="steps",
        learning_rate=args.learning_rate,
        fp16=use_gpu and torch.cuda.is_available(),  # Use mixed precision if GPU available
        report_to=["tensorboard"],
        disable_tqdm=False,
    )
    
    return training_args


def fine_tune(model, tokenizer, train_dataset, eval_dataset, training_args):
    """
    Fine-tune the model using Hugging Face Trainer.
    
    Args:
        model: GPT-2 model
        tokenizer: GPT-2 tokenizer
        train_dataset: Tokenized training dataset
        eval_dataset: Tokenized evaluation dataset (can be None)
        training_args: TrainingArguments object
        
    Returns:
        Trainer: Trained model
    """
    # Data collator for language modeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False  # GPT-2 is causal LM, not masked LM
    )
    
    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )
    
    print(f"\n{'='*60}")
    print("Starting fine-tuning...")
    print('='*60)
    print(f"Training samples: {len(train_dataset)}")
    if eval_dataset:
        print(f"Evaluation samples: {len(eval_dataset)}")
    print(f"Epochs: {training_args.num_train_epochs}")
    print(f"Batch size: {training_args.per_device_train_batch_size}")
    print(f"Learning rate: {training_args.learning_rate}")
    print('='*60 + "\n")
    
    # Train
    trainer.train()
    
    print(f"\n{'='*60}")
    print("✓ Training complete!")
    print('='*60)
    
    return trainer


def save_model(trainer, model, tokenizer, output_dir):
    """
    Save the fine-tuned model and tokenizer.
    
    Args:
        trainer: Trained Trainer object
        model: Fine-tuned model
        tokenizer: Tokenizer
        output_dir (str): Directory to save the model
    """
    print(f"\nSaving model to: {output_dir}")
    
    # Save using trainer (includes optimizer state, etc.)
    trainer.save_model(output_dir)
    
    # Also save tokenizer
    tokenizer.save_pretrained(output_dir)
    
    # Save training config
    config_path = os.path.join(output_dir, 'training_config.json')
    with open(config_path, 'w') as f:
        json.dump({
            'model_name': 'gpt2',
            'num_parameters': sum(p.numel() for p in model.parameters()),
            'vocab_size': len(tokenizer),
        }, f, indent=2)
    
    print(f"✓ Model saved successfully")
    print(f"\nSaved files:")
    for item in os.listdir(output_dir):
        print(f"  - {item}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Fine-tune GPT-2 on math dataset'
    )
    
    # Data arguments
    parser.add_argument(
        '--train_file',
        type=str,
        default='data/train.json',
        help='Training data file (default: data/train.json)'
    )
    parser.add_argument(
        '--test_file',
        type=str,
        default='data/test.json',
        help='Test data file for evaluation (default: data/test.json)'
    )
    
    # Model arguments
    parser.add_argument(
        '--model_name',
        type=str,
        default='gpt2',
        help='Pre-trained model to use (default: gpt2)'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='./fine_tuned_model',
        help='Directory to save fine-tuned model (default: ./fine_tuned_model)'
    )
    
    # Training arguments
    parser.add_argument(
        '--epochs',
        type=int,
        default=3,
        help='Number of training epochs (default: 3)'
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=8,
        help='Training batch size (default: 8)'
    )
    parser.add_argument(
        '--learning_rate',
        type=float,
        default=5e-5,
        help='Learning rate (default: 5e-5)'
    )
    parser.add_argument(
        '--warmup_steps',
        type=int,
        default=500,
        help='Number of warmup steps (default: 500)'
    )
    parser.add_argument(
        '--weight_decay',
        type=float,
        default=0.01,
        help='Weight decay (default: 0.01)'
    )
    parser.add_argument(
        '--max_length',
        type=int,
        default=128,
        help='Maximum sequence length (default: 128)'
    )
    parser.add_argument(
        '--eval_steps',
        type=int,
        default=None,
        help='Evaluation frequency in steps (default: None)'
    )
    parser.add_argument(
        '--log_dir',
        type=str,
        default='./logs',
        help='Directory for training logs (default: ./logs)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("GPT-2 Fine-Tuning on Math Dataset")
    print("="*60)
    print(f"Configuration:")
    print(f"  Model: {args.model_name}")
    print(f"  Training file: {args.train_file}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Learning rate: {args.learning_rate}")
    print(f"  Output directory: {args.output_dir}")
    print("="*60)
    
    # Check GPU
    use_gpu = check_gpu_availability()
    
    # Load model and tokenizer
    model, tokenizer = setup_model_and_tokenizer(args.model_name)
    
    # Load data
    train_dataset, test_dataset = load_data(args.train_file, args.test_file)
    
    # Tokenize datasets
    train_tokenized = tokenize_dataset(train_dataset, tokenizer, args.max_length)
    test_tokenized = None
    if test_dataset:
        test_tokenized = tokenize_dataset(test_dataset, tokenizer, args.max_length)
    
    # Create training arguments
    training_args = create_training_args(args, use_gpu)
    
    # Fine-tune
    trainer = fine_tune(
        model,
        tokenizer,
        train_tokenized,
        test_tokenized,
        training_args
    )
    
    # Save model
    save_model(trainer, model, tokenizer, args.output_dir)
    
    print("\n" + "="*60)
    print("✓ Fine-tuning complete!")
    print("="*60)
    print(f"\nFine-tuned model saved to: {args.output_dir}")
    print(f"Training logs saved to: {args.log_dir}")
    print(f"\nNext step: Run 'python scripts/4_evaluate_models.py'")
    print("\nTo view training logs with TensorBoard:")
    print(f"  tensorboard --logdir {args.log_dir}")


if __name__ == "__main__":
    main()
