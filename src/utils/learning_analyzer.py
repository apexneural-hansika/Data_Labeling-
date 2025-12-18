"""
Learning Analyzer - Analyzes experiences to provide insights and improvements
"""
from typing import Dict, Any, List
from collections import defaultdict
from utils.logger import get_system_logger

logger = get_system_logger()


class LearningAnalyzer:
    """Analyzes stored experiences to identify patterns and improvements."""
    
    def __init__(self, experience_db):
        """
        Initialize learning analyzer.
        
        Args:
            experience_db: ExperienceDatabase instance
        """
        self.experience_db = experience_db
    
    def analyze_performance(self) -> Dict[str, Any]:
        """
        Analyze overall system performance from experiences.
        
        Returns:
            Dictionary with performance insights
        """
        experiences = self.experience_db.experiences
        
        if not experiences:
            return {
                'total_experiences': 0,
                'message': 'No experiences to analyze yet'
            }
        
        # Calculate statistics
        total = len(experiences)
        successful = sum(1 for exp in experiences if exp.get('success', False))
        avg_quality = sum(exp.get('quality_score', 0) for exp in experiences) / total
        avg_time = sum(exp.get('processing_time', 0) for exp in experiences) / total
        
        # Modality breakdown
        modality_stats = defaultdict(lambda: {'count': 0, 'avg_quality': 0, 'success_rate': 0})
        for exp in experiences:
            modality = exp.get('result', {}).get('modality', 'unknown')
            modality_stats[modality]['count'] += 1
            modality_stats[modality]['avg_quality'] += exp.get('quality_score', 0)
            modality_stats[modality]['success'] = modality_stats[modality].get('success', 0) + (1 if exp.get('success') else 0)
        
        for modality in modality_stats:
            count = modality_stats[modality]['count']
            modality_stats[modality]['avg_quality'] /= count
            modality_stats[modality]['success_rate'] = modality_stats[modality]['success'] / count
        
        # Category breakdown
        category_stats = defaultdict(lambda: {'count': 0, 'avg_quality': 0})
        for exp in experiences:
            category = exp.get('result', {}).get('category', 'uncategorized')
            category_stats[category]['count'] += 1
            category_stats[category]['avg_quality'] += exp.get('quality_score', 0)
        
        for category in category_stats:
            category_stats[category]['avg_quality'] /= category_stats[category]['count']
        
        # Extraction method performance
        method_stats = defaultdict(lambda: {'count': 0, 'avg_quality': 0, 'success_rate': 0})
        for exp in experiences:
            method = exp.get('result', {}).get('extraction_method', 'unknown')
            method_stats[method]['count'] += 1
            method_stats[method]['avg_quality'] += exp.get('quality_score', 0)
            method_stats[method]['success'] = method_stats[method].get('success', 0) + (1 if exp.get('success') else 0)
        
        for method in method_stats:
            count = method_stats[method]['count']
            method_stats[method]['avg_quality'] /= count
            method_stats[method]['success_rate'] = method_stats[method]['success'] / count
        
        # Quality trends
        recent_experiences = sorted(experiences, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
        recent_avg_quality = sum(exp.get('quality_score', 0) for exp in recent_experiences) / len(recent_experiences) if recent_experiences else 0
        
        return {
            'total_experiences': total,
            'success_rate': successful / total,
            'avg_quality': avg_quality,
            'avg_processing_time': avg_time,
            'modality_performance': dict(modality_stats),
            'category_performance': dict(category_stats),
            'extraction_method_performance': dict(method_stats),
            'recent_avg_quality': recent_avg_quality,
            'quality_trend': 'improving' if recent_avg_quality > avg_quality else 'stable' if recent_avg_quality == avg_quality else 'declining'
        }
    
    def get_recommendations(self) -> List[str]:
        """
        Get recommendations based on experience analysis.
        
        Returns:
            List of recommendation strings
        """
        analysis = self.analyze_performance()
        recommendations = []
        
        if analysis['total_experiences'] == 0:
            return ["Start processing files to build experience database"]
        
        # Quality recommendations
        if analysis['avg_quality'] < 0.6:
            recommendations.append("Overall quality is low. Consider reviewing extraction methods and prompts.")
        
        if analysis['quality_trend'] == 'declining':
            recommendations.append("Quality trend is declining. Review recent failures and adjust strategies.")
        
        # Modality-specific recommendations
        for modality, stats in analysis['modality_performance'].items():
            if stats['avg_quality'] < 0.6:
                recommendations.append(f"{modality} processing quality is low ({stats['avg_quality']:.2f}). Consider improving {modality} extraction.")
        
        # Method recommendations
        best_method = max(
            analysis['extraction_method_performance'].items(),
            key=lambda x: x[1]['avg_quality'],
            default=(None, {})
        )
        if best_method[0] and best_method[1]['avg_quality'] > 0.7:
            recommendations.append(f"Best performing extraction method: {best_method[0]} (quality: {best_method[1]['avg_quality']:.2f})")
        
        # Success rate recommendations
        if analysis['success_rate'] < 0.8:
            recommendations.append(f"Success rate is {analysis['success_rate']:.1%}. Review error patterns and improve error handling.")
        
        if not recommendations:
            recommendations.append("System is performing well! Keep up the good work.")
        
        return recommendations
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Get comprehensive learning insights.
        
        Returns:
            Dictionary with learning insights
        """
        analysis = self.analyze_performance()
        recommendations = self.get_recommendations()
        
        # Get high-quality examples
        high_quality = self.experience_db.get_high_quality_experiences(min_quality=0.8, limit=5)
        
        return {
            'performance': analysis,
            'recommendations': recommendations,
            'high_quality_examples': [
                {
                    'quality_score': exp.get('quality_score', 0),
                    'modality': exp.get('result', {}).get('modality', 'unknown'),
                    'category': exp.get('result', {}).get('category', 'unknown'),
                    'extraction_method': exp.get('result', {}).get('extraction_method', 'unknown')
                }
                for exp in high_quality
            ],
            'total_learning_examples': len(self.experience_db.experiences)
        }




