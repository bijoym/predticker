"""Alternative ML-free weight optimization using market regime detection.

This approach doesn't rely on ML (to avoid overfitting) but instead learns
optimal weights by testing different combinations on historical data.
"""

from typing import Dict, Tuple, List
import numpy as np
import pandas as pd
from itertools import combinations
import warnings

warnings.filterwarnings("ignore")


class RegimeAdaptiveWeights:
    """Learns weights by testing combinations on historical data."""
    
    def __init__(self):
        """Initialize regime-adaptive weights."""
        self.regime_weights = {}
        self.tested_combinations = {}
        self.is_trained = False
        
    def generate_weight_combinations(self, num_categories: int = 5) -> List[Dict]:
        """Generate weight combinations for testing.
        
        Args:
            num_categories: Number of weight categories (5 for our indicator groups)
        
        Returns:
            List of weight dictionaries to test
        """
        combinations_list = []
        
        # Generate different weight distributions
        # 1. Standard weights (current default)
        combinations_list.append({
            'trend': 0.20,
            'momentum': 0.25,
            'volatility': 0.20,
            'trend_strength': 0.20,
            'stochastic': 0.15,
            'name': 'standard'
        })
        
        # 2. Momentum-heavy (for trending markets)
        combinations_list.append({
            'trend': 0.15,
            'momentum': 0.40,
            'volatility': 0.15,
            'trend_strength': 0.20,
            'stochastic': 0.10,
            'name': 'momentum_heavy'
        })
        
        # 3. Trend-heavy (for strongly directional markets)
        combinations_list.append({
            'trend': 0.35,
            'momentum': 0.15,
            'volatility': 0.20,
            'trend_strength': 0.25,
            'stochastic': 0.05,
            'name': 'trend_heavy'
        })
        
        # 4. Volatility-aware (for choppy markets)
        combinations_list.append({
            'trend': 0.15,
            'momentum': 0.20,
            'volatility': 0.35,
            'trend_strength': 0.15,
            'stochastic': 0.15,
            'name': 'volatility_aware'
        })
        
        # 5. ADX-focused (for strong trends only)
        combinations_list.append({
            'trend': 0.15,
            'momentum': 0.20,
            'volatility': 0.15,
            'trend_strength': 0.40,
            'stochastic': 0.10,
            'name': 'adx_focused'
        })
        
        # 6. Balanced momentum/volatility
        combinations_list.append({
            'trend': 0.20,
            'momentum': 0.30,
            'volatility': 0.25,
            'trend_strength': 0.15,
            'stochastic': 0.10,
            'name': 'balanced'
        })
        
        return combinations_list
    
    def detect_market_regime(self, features: Dict[str, float]) -> str:
        """Detect market regime from features.
        
        Args:
            features: Technical indicator values
        
        Returns:
            Regime name: 'trending_strong', 'trending_weak', 'ranging', 'volatile'
        """
        adx = features.get('adx', 20)
        atr_percent = features.get('atr_percent', 1.5)
        bb_position = features.get('bb_position', 0.5)
        rsi = features.get('rsi', 50)
        
        # Determine regime
        if adx > 30:
            if atr_percent > 2.5:
                return 'trending_strong_high_vol'
            else:
                return 'trending_strong_low_vol'
        elif adx > 20:
            if atr_percent > 2.5:
                return 'trending_weak_high_vol'
            else:
                return 'trending_weak_low_vol'
        else:
            if atr_percent > 2.5:
                return 'ranging_high_vol'
            else:
                return 'ranging_low_vol'
    
    def test_weight_combination(self,
                               weight_combo: Dict,
                               features_list: List[Dict],
                               predictions_list: List[Dict]) -> float:
        """Test a weight combination on historical data.
        
        Args:
            weight_combo: Dictionary with weights
            features_list: List of feature dictionaries
            predictions_list: List of prediction results
        
        Returns:
            Accuracy percentage (0-100)
        """
        if len(features_list) != len(predictions_list):
            return 0.0
        
        correct_count = 0
        
        for features, actual in zip(features_list, predictions_list):
            try:
                # Calculate weighted score with these weights
                trend_score = 1 if features.get('slope', 0) > 0 else 0
                trend_score += 1 if features.get('sma_20', 0) > features.get('sma_50', 0) else 0
                trend_normalized = trend_score / 3.0
                
                rsi = features.get('rsi', 50)
                momentum_score = 0
                if rsi < 30:
                    momentum_score = 1.0
                elif rsi < 50:
                    momentum_score = 0.5
                elif rsi > 70:
                    momentum_score = 0.0
                else:
                    momentum_score = 0.5
                momentum_normalized = momentum_score
                
                bb_position = features.get('bb_position', 0.5)
                volatility_normalized = 1.0 - abs(bb_position - 0.5) * 2
                volatility_normalized = max(0, min(1, volatility_normalized))
                
                adx = features.get('adx', 20)
                trend_strength_normalized = min(adx / 40.0, 1.0)
                
                k_stoch = features.get('k_stoch', 50)
                stoch_normalized = 0.5 if 20 < k_stoch < 80 else (1.0 if k_stoch < 20 else 0.0)
                
                # Apply weights
                final_score = (
                    trend_normalized * weight_combo['trend'] +
                    momentum_normalized * weight_combo['momentum'] +
                    volatility_normalized * weight_combo['volatility'] +
                    trend_strength_normalized * weight_combo['trend_strength'] +
                    stoch_normalized * weight_combo['stochastic']
                )
                
                predicted = 1 if final_score > 0.5 else 0
                actual_dir = actual.get('actual', 0)
                
                if predicted == actual_dir:
                    correct_count += 1
                    
            except Exception:
                continue
        
        accuracy = (correct_count / len(predictions_list)) * 100 if len(predictions_list) > 0 else 0.0
        return accuracy
    
    def train(self, 
             features_list: List[Dict],
             predictions_list: List[Dict]):
        """Train by testing weight combinations.
        
        Args:
            features_list: List of feature dictionaries
            predictions_list: List of prediction results
        """
        print("\n" + "="*70)
        print("REGIME-ADAPTIVE WEIGHTS - OPTIMIZATION")
        print("="*70)
        
        combinations = self.generate_weight_combinations()
        
        print(f"\nTesting {len(combinations)} weight combinations...")
        print(f"Historical samples: {len(features_list)}")
        
        # Test each combination
        for combo in combinations:
            accuracy = self.test_weight_combination(combo, features_list, predictions_list)
            combo['accuracy'] = accuracy
            self.tested_combinations[combo['name']] = {
                'weights': {k: v for k, v in combo.items() if k not in ['name', 'accuracy']},
                'accuracy': accuracy
            }
            print(f"\n{combo['name']:30s} → {accuracy:6.2f}%")
        
        # Find best combinations per regime
        print("\n" + "="*70)
        print("RECOMMENDATION BY REGIME")
        print("="*70)
        
        regimes = ['trending_strong_high_vol', 'trending_strong_low_vol', 
                   'trending_weak_high_vol', 'trending_weak_low_vol',
                   'ranging_high_vol', 'ranging_low_vol']
        
        best_combos = sorted(combinations, key=lambda x: x['accuracy'], reverse=True)
        
        self.regime_weights['trending_strong'] = best_combos[0]
        self.regime_weights['trending_weak'] = best_combos[0]
        self.regime_weights['ranging'] = best_combos[2] if len(best_combos) > 2 else best_combos[0]
        self.regime_weights['ranging_high'] = best_combos[2] if len(best_combos) > 2 else best_combos[0]
        
        print(f"Best for Strong Trends: {self.regime_weights['trending_strong']['name']} "
              f"({self.regime_weights['trending_strong']['accuracy']:.2f}%)")
        print(f"Best for Weak Trends: {self.regime_weights['trending_weak']['name']} "
              f"({self.regime_weights['trending_weak']['accuracy']:.2f}%)")
        print(f"Best for Ranging: {self.regime_weights['ranging']['name']} "
              f"({self.regime_weights['ranging']['accuracy']:.2f}%)")
        
        # Calculate improvement
        baseline = next((c['accuracy'] for c in combinations if c['name'] == 'standard'), 0)
        best_accuracy = best_combos[0]['accuracy']
        improvement = best_accuracy - baseline
        
        print(f"\nImprovement: {improvement:+.2f}% (baseline: {baseline:.2f}% → best: {best_accuracy:.2f}%)")
        
        self.is_trained = True
    
    def get_adaptive_weights(self, features: Dict[str, float]) -> Dict[str, float]:
        """Get weights for current market conditions.
        
        Args:
            features: Technical indicator values
        
        Returns:
            Weights dictionary
        """
        if not self.is_trained:
            return self._default_weights()
        
        # Detect regime
        regime = self.detect_market_regime(features)
        
        # Map complex regime to simple category
        if 'strong' in regime:
            weights = self.regime_weights.get('trending_strong', {})
        elif 'weak' in regime:
            weights = self.regime_weights.get('trending_weak', {})
        elif 'high_vol' in regime:
            weights = self.regime_weights.get('ranging_high', {})
        else:
            weights = self.regime_weights.get('ranging', {})
        
        if not weights:
            return self._default_weights()
        
        return {
            'trend': weights.get('trend', 0.20),
            'momentum': weights.get('momentum', 0.25),
            'volatility': weights.get('volatility', 0.20),
            'trend_strength': weights.get('trend_strength', 0.20),
            'stochastic': weights.get('stochastic', 0.15)
        }
    
    def _default_weights(self) -> Dict[str, float]:
        """Return default static weights."""
        return {
            'trend': 0.20,
            'momentum': 0.25,
            'volatility': 0.20,
            'trend_strength': 0.20,
            'stochastic': 0.15
        }
    
    def save_weights(self, filepath: str):
        """Save optimized weights to file."""
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump({
                'regime_weights': self.regime_weights,
                'tested_combinations': self.tested_combinations,
                'is_trained': self.is_trained
            }, f)
        print(f"Weights saved to {filepath}")
    
    def load_weights(self, filepath: str):
        """Load optimized weights from file."""
        import pickle
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.regime_weights = data['regime_weights']
            self.tested_combinations = data['tested_combinations']
            self.is_trained = data['is_trained']
        print(f"Weights loaded from {filepath}")


if __name__ == "__main__":
    print("Regime-Adaptive Weights Optimizer")
    print("Usage: from src.regime_weights import RegimeAdaptiveWeights")
