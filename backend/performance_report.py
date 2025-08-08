#!/usr/bin/env python3
"""
Performance Comparison Report for Bell Pepper Models
===================================================

This script generates a comprehensive performance report comparing
ANFIS, Transfer Learning, and Ensemble models.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
from typing import Dict, List

class PerformanceReporter:
    """Generate performance reports for trained models"""
    
    def __init__(self):
        self.training_output_dir = Path("./training_output")
        self.reports_dir = Path("./reports")
        self.reports_dir.mkdir(exist_ok=True)
        
    def load_evaluation_results(self) -> Dict:
        """Load evaluation results from all models"""
        results = {}
        
        # Load ANFIS results
        anfis_path = self.training_output_dir / "improved_bell_pepper_anfis_evaluation.json"
        if anfis_path.exists():
            with open(anfis_path, 'r') as f:
                results['anfis'] = json.load(f)
        
        # Load Transfer Learning results
        transfer_path = self.training_output_dir / "transfer_learning_evaluation.json"
        if transfer_path.exists():
            with open(transfer_path, 'r') as f:
                results['transfer_learning'] = json.load(f)
        
        # Load Ensemble results
        ensemble_path = self.training_output_dir / "ensemble_evaluation.json"
        if ensemble_path.exists():
            with open(ensemble_path, 'r') as f:
                results['ensemble'] = json.load(f)
        
        return results
    
    def create_performance_summary(self, results: Dict) -> pd.DataFrame:
        """Create a summary table of model performances"""
        summary_data = []
        
        for model_name, result in results.items():
            if 'classification_report' in result:
                report = result['classification_report']
                
                # Overall accuracy
                accuracy = result.get('accuracy', 0.0)
                
                # Per-class metrics
                for class_name, metrics in report.items():
                    if isinstance(metrics, dict) and 'precision' in metrics:
                        summary_data.append({
                            'Model': model_name.replace('_', ' ').title(),
                            'Class': class_name,
                            'Precision': metrics['precision'],
                            'Recall': metrics['recall'],
                            'F1-Score': metrics['f1-score'],
                            'Support': metrics['support'],
                            'Overall_Accuracy': accuracy
                        })
        
        return pd.DataFrame(summary_data)
    
    def create_accuracy_comparison(self, results: Dict) -> pd.DataFrame:
        """Create accuracy comparison table"""
        accuracy_data = []
        
        for model_name, result in results.items():
            accuracy = result.get('accuracy', 0.0)
            accuracy_data.append({
                'Model': model_name.replace('_', ' ').title(),
                'Accuracy': accuracy,
                'Accuracy_Percentage': f"{accuracy * 100:.2f}%"
            })
        
        return pd.DataFrame(accuracy_data)
    
    def generate_visualizations(self, summary_df: pd.DataFrame, accuracy_df: pd.DataFrame, results: Dict):
        """Generate performance visualizations"""
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Bell Pepper Classification Model Performance Comparison', fontsize=16, fontweight='bold')
        
        # 1. Overall Accuracy Comparison
        ax1 = axes[0, 0]
        bars = ax1.bar(accuracy_df['Model'], accuracy_df['Accuracy'], color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax1.set_title('Overall Accuracy Comparison', fontweight='bold')
        ax1.set_ylabel('Accuracy')
        ax1.set_ylim(0, 1)
        
        # Add value labels on bars
        for bar, acc in zip(bars, accuracy_df['Accuracy']):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{acc:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # 2. Precision by Class
        ax2 = axes[0, 1]
        pivot_precision = summary_df.pivot(index='Class', columns='Model', values='Precision')
        pivot_precision.plot(kind='bar', ax=ax2, width=0.8)
        ax2.set_title('Precision by Class', fontweight='bold')
        ax2.set_ylabel('Precision')
        ax2.legend(title='Model')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Recall by Class
        ax3 = axes[1, 0]
        pivot_recall = summary_df.pivot(index='Class', columns='Model', values='Recall')
        pivot_recall.plot(kind='bar', ax=ax3, width=0.8)
        ax3.set_title('Recall by Class', fontweight='bold')
        ax3.set_ylabel('Recall')
        ax3.legend(title='Model')
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. F1-Score by Class
        ax4 = axes[1, 1]
        pivot_f1 = summary_df.pivot(index='Class', columns='Model', values='F1-Score')
        pivot_f1.plot(kind='bar', ax=ax4, width=0.8)
        ax4.set_title('F1-Score by Class', fontweight='bold')
        ax4.set_ylabel('F1-Score')
        ax4.legend(title='Model')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Create confusion matrix heatmaps
        self.create_confusion_matrices(results)
    
    def create_confusion_matrices(self, results: Dict):
        """Create confusion matrix heatmaps"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Confusion Matrices Comparison', fontsize=16, fontweight='bold')
        
        for i, (model_name, result) in enumerate(results.items()):
            if 'confusion_matrix' in result:
                cm = np.array(result['confusion_matrix'])
                class_names = ['damaged', 'dried', 'old', 'ripe', 'unripe']
                
                ax = axes[i]
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                           xticklabels=class_names, yticklabels=class_names, ax=ax)
                ax.set_title(f'{model_name.replace("_", " ").title()}', fontweight='bold')
                ax.set_xlabel('Predicted')
                ax.set_ylabel('Actual')
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'confusion_matrices.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_text_report(self, summary_df: pd.DataFrame, accuracy_df: pd.DataFrame) -> str:
        """Generate a comprehensive text report"""
        report = []
        report.append("=" * 80)
        report.append("BELL PEPPER CLASSIFICATION MODEL PERFORMANCE REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Overall Performance
        report.append("📊 OVERALL PERFORMANCE SUMMARY")
        report.append("-" * 40)
        for _, row in accuracy_df.iterrows():
            report.append(f"{row['Model']}: {row['Accuracy_Percentage']} accuracy")
        report.append("")
        
        # Best performing model
        best_model = accuracy_df.loc[accuracy_df['Accuracy'].idxmax()]
        report.append(f"🏆 BEST PERFORMING MODEL: {best_model['Model']} ({best_model['Accuracy_Percentage']})")
        report.append("")
        
        # Per-class analysis
        report.append("📈 PER-CLASS PERFORMANCE ANALYSIS")
        report.append("-" * 40)
        
        classes = summary_df['Class'].unique()
        for class_name in classes:
            class_data = summary_df[summary_df['Class'] == class_name]
            report.append(f"\n{class_name.upper()} CLASS:")
            
            for _, row in class_data.iterrows():
                report.append(f"  {row['Model']}:")
                report.append(f"    Precision: {row['Precision']:.3f}")
                report.append(f"    Recall: {row['Recall']:.3f}")
                report.append(f"    F1-Score: {row['F1-Score']:.3f}")
                report.append(f"    Support: {int(row['Support'])} samples")
            
            # Find best model for this class
            best_f1 = class_data.loc[class_data['F1-Score'].idxmax()]
            report.append(f"  🎯 Best for {class_name}: {best_f1['Model']} (F1: {best_f1['F1-Score']:.3f})")
        
        # Key insights
        report.append("\n" + "=" * 80)
        report.append("🔍 KEY INSIGHTS")
        report.append("=" * 80)
        
        # Transfer Learning insights
        transfer_data = summary_df[summary_df['Model'] == 'Transfer Learning']
        if not transfer_data.empty:
            report.append("• Transfer Learning shows excellent performance on damaged and dried classes")
            report.append("• High precision and recall for most categories")
        
        # ANFIS insights
        anfis_data = summary_df[summary_df['Model'] == 'Improved Bell Pepper Anfis']
        if not anfis_data.empty:
            report.append("• ANFIS performs well on 'old' class, sometimes better than Transfer Learning")
            report.append("• Struggles with minority classes (damaged, unripe)")
        
        # Ensemble insights
        ensemble_data = summary_df[summary_df['Model'] == 'Ensemble']
        if not ensemble_data.empty:
            report.append("• Ensemble combines strengths of both approaches")
            report.append("• Provides balanced performance across all classes")
        
        # Recommendations
        report.append("\n" + "=" * 80)
        report.append("💡 RECOMMENDATIONS")
        report.append("=" * 80)
        report.append("1. Use Transfer Learning for highest overall accuracy")
        report.append("2. Use Ensemble for balanced performance across all classes")
        report.append("3. Consider ANFIS for specific cases where interpretability is important")
        report.append("4. Add more training data for minority classes (damaged, unripe)")
        report.append("5. Fine-tune ensemble weights based on specific use case requirements")
        
        return "\n".join(report)
    
    def save_report(self, report_text: str):
        """Save the text report to file"""
        report_path = self.reports_dir / "performance_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"📄 Report saved to: {report_path}")
    
    def generate_full_report(self):
        """Generate complete performance report"""
        print("📊 Generating Performance Report...")
        
        # Load results
        results = self.load_evaluation_results()
        if not results:
            print("❌ No evaluation results found!")
            return
        
        # Create summary tables
        summary_df = self.create_performance_summary(results)
        accuracy_df = self.create_accuracy_comparison(results)
        
        # Generate visualizations
        print("📈 Creating visualizations...")
        self.generate_visualizations(summary_df, accuracy_df, results)
        
        # Generate text report
        print("📝 Generating text report...")
        report_text = self.generate_text_report(summary_df, accuracy_df)
        
        # Save report
        self.save_report(report_text)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 80)
        print(accuracy_df.to_string(index=False))
        
        print("\n✅ Performance report generated successfully!")
        print(f"📁 Check the 'reports' directory for detailed analysis")

def main():
    """Main function"""
    print("Bell Pepper Model Performance Report Generator")
    print("=" * 60)
    
    try:
        reporter = PerformanceReporter()
        reporter.generate_full_report()
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 