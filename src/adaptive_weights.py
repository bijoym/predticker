"""Adaptive weight optimizer using machine learning.

This module learns optimal indicator weights from historical backtest performance
using XGBoost and RandomForest models. Weights are adjusted based on market regime.
"""

from typing import Dict, Tuple, List
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings

warnings.filterwarnings("ignore")


class AdaptiveWeightOptimizer:
    """Learn indicator weights from historical performance data."""
    
    def __init__(self, model_type: str = "random_forest"):
        """Initialize optimizer with specified model.
        
        Args:
            model_type: "random_forest" or "xgboost"
        """
        self.model_type = model_type
        self.models = {}  # Separate model for each weight category
        self.scalers = {}
        self.feature_names = None
        self.is_trained = False
        
    def prepare_training_data(self, 
                            predictions_df: pd.DataFrame,
                            features_history: List[Dict]) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for training from backtest predictions.
        
        Args:
            predictions_df: DataFrame with columns [predicted, actual, correct, price_change]
            features_history: List of feature dicts from compute_enhanced_features calls
        
        Returns:
            Tuple of (X features, y targets - whether prediction was correct)
        """
        # Convert features list to DataFrame
        features_df = pd.DataFrame(features_history)
        
        # Target: 1 if prediction was correct, 0 otherwise
        y = (predictions_df['correct'].values).astype(int)
        
        # Features: all technical indicators
        X = features_df[[col for col in features_df.columns if col not in ['price', 'avg_volume']]]
        
        self.feature_names = X.columns.tolist()
        
        return X, y
    
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2):
        """Train models to predict indicator importance.
        
        Args:
            X: Feature matrix with technical indicators
            y: Target values (1 = correct prediction, 0 = incorrect)
            test_size: Proportion of data for testing
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        if self.model_type == "random_forest":
            model = RandomForestRegressor(
                n_estimators=50,  # Reduced from 100
                max_depth=5,  # Reduced from 10 - prevent overfitting
                min_samples_split=10,  # Increased from 5
                min_samples_leaf=5,  # Increased from 2
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        print(f"\n{'='*70}")
        print(f"ADAPTIVE WEIGHT OPTIMIZER - MODEL TRAINING")
        print(f"{'='*70}")
        print(f"Model Type: {self.model_type}")
        print(f"Training Samples: {len(X_train)}")
        print(f"Test Samples: {len(X_test)}")
        print(f"Train Score (R²): {train_score:.4f}")
        print(f"Test Score (R²): {test_score:.4f}")
        
        # Store model and scaler
        self.models['main'] = model
        self.scalers['main'] = scaler
        self.is_trained = True
        
        return train_score, test_score
    
    def get_adaptive_weights(self, features: Dict[str, float]) -> Dict[str, float]:
        """Get adaptive weights based on current market features.
        
        Args:
            features: Current technical indicator values
        
        Returns:
            Dict with adaptive weights for each indicator category
        """
        if not self.is_trained:
            return self._default_weights()
        
        # Prepare features for prediction
        feature_values = np.array([features.get(name, 0.0) for name in self.feature_names]).reshape(1, -1)
        
        # Scale features
        scaler = self.scalers['main']
        feature_scaled = scaler.transform(feature_values)
        
        # Get feature importance from model
        model = self.models['main']
        importances = model.feature_importances_
        
        # Map importance to indicator categories
        weights = self._map_importance_to_weights(importances, features)
        
        return weights
    
    def _map_importance_to_weights(self, importances: np.ndarray, features: Dict) -> Dict[str, float]:
        """Map feature importance scores to weight categories.
        
        Args:
            importances: Feature importance from model
            features: Current feature values
        
        Returns:
            Dict with weights for each category
        """
        weights = {
            'trend': 0.0,
            'momentum': 0.0,
            'volatility': 0.0,
            'trend_strength': 0.0,
            'stochastic': 0.0
        }
        
        # Map features to categories
        category_mapping = {
            'trend': ['slope', 'sma_20', 'sma_50', 'ema_12', 'ema_26'],
            'momentum': ['rsi', 'macd', 'macd_signal', 'macd_histogram'],
            'volatility': ['bb_position', 'atr_percent', 'volatility'],
            'trend_strength': ['adx'],
            'stochastic': ['k_stoch', 'd_stoch']
        }
        
        # Accumulate importance scores for each category
        for category, feature_list in category_mapping.items():
            score = 0.0
            count = 0
            for feature in feature_list:
                if feature in self.feature_names:
                    idx = self.feature_names.index(feature)
                    if idx < len(importances):
                        score += importances[idx]
                        count += 1
            if count > 0:
                weights[category] = score / count
        
        # Normalize weights to sum to 1
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        else:
            weights = self._default_weights()
        
        return weights
    
    def _default_weights(self) -> Dict[str, float]:
        """Return default static weights."""
        return {
            'trend': 0.20,
            'momentum': 0.25,
            'volatility': 0.20,
            'trend_strength': 0.20,
            'stochastic': 0.15
        }
    
    def get_regime_specific_weights(self, 
                                   features: Dict[str, float],
                                   volatility_level: str = 'normal') -> Dict[str, float]:
        """Get weights adjusted for market regime.
        
        Args:
            features: Current technical indicator values
            volatility_level: 'low', 'normal', 'high'
        
        Returns:
            Regime-adjusted weights
        """
        adaptive_weights = self.get_adaptive_weights(features)
        
        # Adjust for volatility regime
        if volatility_level == 'high':
            # In high volatility: prioritize trend strength (ADX) and volatility measures
            adaptive_weights['trend_strength'] = min(0.35, adaptive_weights['trend_strength'] * 1.5)
            adaptive_weights['volatility'] = min(0.30, adaptive_weights['volatility'] * 1.3)
            adaptive_weights['momentum'] = max(0.15, adaptive_weights['momentum'] * 0.8)
        
        elif volatility_level == 'low':
            # In low volatility: prioritize momentum and trend
            adaptive_weights['momentum'] = min(0.35, adaptive_weights['momentum'] * 1.3)
            adaptive_weights['trend'] = min(0.30, adaptive_weights['trend'] * 1.2)
            adaptive_weights['volatility'] = max(0.10, adaptive_weights['volatility'] * 0.7)
        
        # Renormalize
        total = sum(adaptive_weights.values())
        if total > 0:
            adaptive_weights = {k: v / total for k, v in adaptive_weights.items()}
        
        return adaptive_weights
    
    def save_model(self, filepath: str):
        """Save trained model to file."""
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.models.get('main'),
                'scaler': self.scalers.get('main'),
                'feature_names': self.feature_names,
                'model_type': self.model_type
            }, f)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file."""
        import pickle
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.models['main'] = data['model']
            self.scalers['main'] = data['scaler']
            self.feature_names = data['feature_names']
            self.model_type = data['model_type']
            self.is_trained = True
        print(f"Model loaded from {filepath}")


def create_training_dataset_from_backtest(backtest_results: Dict) -> Tuple[pd.DataFrame, pd.Series]:
    """Create training dataset from backtest results.
    
    Args:
        backtest_results: Results dict from backtest_ticker()
    
    Returns:
        Tuple of (X features, y targets)
    """
    predictions_df = backtest_results.get('predictions_df')
    
    if predictions_df is None or len(predictions_df) == 0:
        raise ValueError("No prediction history in backtest results")
    
    # Target: 1 if correct, 0 if incorrect
    y = (predictions_df['correct'].values).astype(int)
    
    # For now, use simple features from predictions
    # In production, would reconstruct full feature history
    X = pd.DataFrame({
        'price_change': predictions_df['price_change'].values,
    })
    
    return X, y


if __name__ == "__main__":
    # Example usage
    print("Adaptive Weight Optimizer Module")
    print("Usage: from src.adaptive_weights import AdaptiveWeightOptimizer")
    print("\nExample:")
    print("  optimizer = AdaptiveWeightOptimizer()")
    print("  optimizer.train(X_train, y_train)")
    print("  weights = optimizer.get_adaptive_weights(features)")
    print("  regime_weights = optimizer.get_regime_specific_weights(features, 'high')")
