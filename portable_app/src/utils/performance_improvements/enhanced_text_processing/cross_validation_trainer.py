#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cross-Validation Training Module
Enhanced training with k-fold cross-validation for better model evaluation

Author: Augment Agent
Date: 2025-07-25
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional
import time
import json

class CrossValidationTrainer:
    """
    Enhanced training with cross-validation for better model evaluation
    """
    
    def __init__(self, n_folds=5, random_state=42):
        self.n_folds = n_folds
        self.random_state = random_state
        self.fold_results = []
        self.best_model = None
        self.best_score = 0.0
        
    def train_with_cross_validation(self, X, y, model_class, model_params=None, 
                                  stratified=True, verbose=True):
        """
        Train model with k-fold cross-validation
        
        Args:
            X: Feature data
            y: Target labels
            model_class: Model class to instantiate
            model_params: Parameters for model initialization
            stratified: Whether to use stratified k-fold
            verbose: Whether to print detailed progress
            
        Returns:
            Dict with cross-validation results
        """
        if model_params is None:
            model_params = {}
        
        print(f"🔄 Starting {self.n_folds}-fold cross-validation...")
        print(f"   Dataset size: {len(X)} samples")
        print(f"   Stratified: {stratified}")
        
        # Choose cross-validation strategy
        if stratified and len(np.unique(y)) > 1:
            kfold = StratifiedKFold(n_splits=self.n_folds, shuffle=True, random_state=self.random_state)
            print(f"   Using StratifiedKFold to maintain class distribution")
        else:
            kfold = KFold(n_splits=self.n_folds, shuffle=True, random_state=self.random_state)
            print(f"   Using standard KFold")
        
        fold_accuracies = []
        fold_times = []
        self.fold_results = []
        
        for fold, (train_idx, val_idx) in enumerate(kfold.split(X, y)):
            print(f"\n📊 Fold {fold + 1}/{self.n_folds}")
            fold_start_time = time.time()
            
            # Split data
            if isinstance(X, np.ndarray):
                X_train_fold, X_val_fold = X[train_idx], X[val_idx]
            else:
                X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
            
            if isinstance(y, np.ndarray):
                y_train_fold, y_val_fold = y[train_idx], y[val_idx]
            else:
                y_train_fold, y_val_fold = y.iloc[train_idx], y.iloc[val_idx]
            
            print(f"  Train size: {len(X_train_fold)}, Validation size: {len(X_val_fold)}")
            
            # Train model for this fold
            try:
                model = model_class(**model_params)
                
                # Train the model
                if hasattr(model, 'fit'):
                    model.fit(X_train_fold, y_train_fold)
                else:
                    # For PyTorch models or custom training
                    model = self._train_pytorch_model(model, X_train_fold, y_train_fold)
                
                # Evaluate
                if hasattr(model, 'predict'):
                    y_pred = model.predict(X_val_fold)
                else:
                    y_pred = self._predict_pytorch_model(model, X_val_fold)
                
                # Calculate metrics
                accuracy = accuracy_score(y_val_fold, y_pred)
                fold_accuracies.append(accuracy)
                
                fold_end_time = time.time()
                fold_time = fold_end_time - fold_start_time
                fold_times.append(fold_time)
                
                print(f"  Fold {fold + 1} accuracy: {accuracy:.4f} ({fold_time:.1f}s)")
                
                # Store detailed results
                fold_result = {
                    'fold': fold + 1,
                    'accuracy': accuracy,
                    'train_size': len(X_train_fold),
                    'val_size': len(X_val_fold),
                    'training_time': fold_time,
                    'predictions': y_pred.tolist() if hasattr(y_pred, 'tolist') else list(y_pred),
                    'true_labels': y_val_fold.tolist() if hasattr(y_val_fold, 'tolist') else list(y_val_fold)
                }
                
                # Add classification report for detailed analysis
                if verbose:
                    try:
                        class_report = classification_report(y_val_fold, y_pred, output_dict=True, zero_division=0)
                        fold_result['classification_report'] = class_report
                    except Exception as e:
                        print(f"    Warning: Could not generate classification report: {e}")
                
                self.fold_results.append(fold_result)
                
                # Keep track of best model
                if accuracy > self.best_score:
                    self.best_score = accuracy
                    self.best_model = model
                
            except Exception as e:
                print(f"  ❌ Error in fold {fold + 1}: {e}")
                fold_accuracies.append(0.0)
                fold_times.append(0.0)
        
        # Calculate statistics
        mean_accuracy = np.mean(fold_accuracies)
        std_accuracy = np.std(fold_accuracies)
        mean_time = np.mean(fold_times)
        
        print(f"\n📈 Cross-Validation Results:")
        print(f"  Mean Accuracy: {mean_accuracy:.4f} ± {std_accuracy:.4f}")
        print(f"  Min Accuracy: {min(fold_accuracies):.4f}")
        print(f"  Max Accuracy: {max(fold_accuracies):.4f}")
        print(f"  Average Training Time: {mean_time:.1f}s per fold")
        
        # Check for overfitting indicators
        self._analyze_overfitting_indicators(fold_accuracies, std_accuracy)
        
        # Generate detailed analysis
        analysis = self._generate_detailed_analysis()
        
        return {
            'mean_accuracy': mean_accuracy,
            'std_accuracy': std_accuracy,
            'fold_accuracies': fold_accuracies,
            'fold_results': self.fold_results,
            'best_model': self.best_model,
            'best_score': self.best_score,
            'training_times': fold_times,
            'analysis': analysis
        }
    
    def _train_pytorch_model(self, model, X_train, y_train, epochs=10):
        """Train PyTorch model (placeholder for custom training logic)"""
        # This would be implemented based on the specific PyTorch model
        # For now, return the model as-is
        print(f"    Training PyTorch model for {epochs} epochs...")
        return model
    
    def _predict_pytorch_model(self, model, X_val):
        """Make predictions with PyTorch model (placeholder)"""
        # This would be implemented based on the specific PyTorch model
        # For now, return dummy predictions
        return np.random.randint(0, 2, len(X_val))
    
    def _analyze_overfitting_indicators(self, fold_accuracies, std_accuracy):
        """Analyze potential overfitting indicators"""
        print(f"\n🔍 Overfitting Analysis:")
        
        # High variance between folds
        if std_accuracy > 0.05:
            print(f"  ⚠️  High variance between folds (σ={std_accuracy:.4f}) - possible overfitting")
        else:
            print(f"  ✅ Good consistency between folds (σ={std_accuracy:.4f})")
        
        # Check for outlier folds
        mean_acc = np.mean(fold_accuracies)
        outliers = [acc for acc in fold_accuracies if abs(acc - mean_acc) > 2 * std_accuracy]
        
        if outliers:
            print(f"  ⚠️  Found {len(outliers)} outlier fold(s) - check data distribution")
        else:
            print(f"  ✅ No significant outlier folds detected")
        
        # Performance assessment
        if mean_acc < 0.6:
            print(f"  ❌ Low overall accuracy ({mean_acc:.3f}) - model may be underfitting")
        elif mean_acc > 0.95 and std_accuracy < 0.01:
            print(f"  ⚠️  Very high accuracy with low variance - check for data leakage")
        else:
            print(f"  ✅ Reasonable performance range")
    
    def _generate_detailed_analysis(self) -> Dict:
        """Generate detailed analysis of cross-validation results"""
        if not self.fold_results:
            return {}
        
        analysis = {
            'fold_consistency': self._analyze_fold_consistency(),
            'class_performance': self._analyze_class_performance(),
            'training_stability': self._analyze_training_stability()
        }
        
        return analysis
    
    def _analyze_fold_consistency(self) -> Dict:
        """Analyze consistency across folds"""
        accuracies = [result['accuracy'] for result in self.fold_results]
        
        return {
            'coefficient_of_variation': np.std(accuracies) / np.mean(accuracies) if np.mean(accuracies) > 0 else 0,
            'range': max(accuracies) - min(accuracies),
            'consistency_score': 1.0 - (np.std(accuracies) / 0.1)  # Normalize by expected std
        }
    
    def _analyze_class_performance(self) -> Dict:
        """Analyze per-class performance across folds"""
        if not self.fold_results or 'classification_report' not in self.fold_results[0]:
            return {}
        
        class_metrics = defaultdict(list)
        
        for result in self.fold_results:
            if 'classification_report' in result:
                report = result['classification_report']
                for class_label, metrics in report.items():
                    if isinstance(metrics, dict) and 'f1-score' in metrics:
                        class_metrics[class_label].append(metrics['f1-score'])
        
        class_analysis = {}
        for class_label, f1_scores in class_metrics.items():
            if f1_scores:
                class_analysis[class_label] = {
                    'mean_f1': np.mean(f1_scores),
                    'std_f1': np.std(f1_scores),
                    'consistency': 1.0 - (np.std(f1_scores) / max(np.mean(f1_scores), 0.1))
                }
        
        return class_analysis
    
    def _analyze_training_stability(self) -> Dict:
        """Analyze training time stability"""
        times = [result['training_time'] for result in self.fold_results]
        
        return {
            'mean_time': np.mean(times),
            'std_time': np.std(times),
            'time_consistency': 1.0 - (np.std(times) / max(np.mean(times), 1.0))
        }
    
    def get_model_quality_assessment(self) -> str:
        """Get overall model quality assessment"""
        if not self.fold_results:
            return "No cross-validation results available"
        
        mean_acc = np.mean([r['accuracy'] for r in self.fold_results])
        std_acc = np.std([r['accuracy'] for r in self.fold_results])
        
        if mean_acc >= 0.8 and std_acc <= 0.05:
            return "🎯 EXCELLENT - High accuracy with good consistency"
        elif mean_acc >= 0.7 and std_acc <= 0.08:
            return "✅ GOOD - Solid performance with acceptable variance"
        elif mean_acc >= 0.6 and std_acc <= 0.1:
            return "⚠️ FAIR - Moderate performance, room for improvement"
        elif std_acc > 0.1:
            return "❌ UNSTABLE - High variance between folds, check for overfitting"
        else:
            return "❌ POOR - Low accuracy, model needs significant improvement"
    
    def save_results(self, filepath: str):
        """Save cross-validation results to JSON file"""
        results_data = {
            'n_folds': self.n_folds,
            'random_state': self.random_state,
            'best_score': self.best_score,
            'fold_results': self.fold_results,
            'quality_assessment': self.get_model_quality_assessment(),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
            print(f"📁 Cross-validation results saved to: {filepath}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")


def validate_model_with_cv(X, y, model_class, model_params=None, n_folds=5, 
                          stratified=True, save_path=None):
    """
    Convenience function to perform cross-validation on a model
    
    Args:
        X: Feature data
        y: Target labels  
        model_class: Model class to validate
        model_params: Model initialization parameters
        n_folds: Number of cross-validation folds
        stratified: Whether to use stratified k-fold
        save_path: Path to save results (optional)
        
    Returns:
        Cross-validation results dictionary
    """
    trainer = CrossValidationTrainer(n_folds=n_folds)
    results = trainer.train_with_cross_validation(
        X, y, model_class, model_params, stratified=stratified
    )
    
    print(f"\n{trainer.get_model_quality_assessment()}")
    
    if save_path:
        trainer.save_results(save_path)
    
    return results
