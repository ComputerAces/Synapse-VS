import numpy as np

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

'\nData Science Nodes (Local ML).\n\nAnomaly Detection: Isolation Forest (sklearn).\nLinear Regression: Simple Prediction (sklearn).\n\nDependencies (Lazy): scikit-learn (sklearn), numpy.\n'

IsolationForest = None

LinearRegression = None

def ensure_sklearn():
    global IsolationForest, LinearRegression
    if IsolationForest:
        return True
    if DependencyManager.ensure('scikit-learn', 'sklearn'):
        from sklearn.ensemble import IsolationForest as _IF
        from sklearn.linear_model import LinearRegression as _LR
        IsolationForest = _IF
        LinearRegression = _LR
        return True
    return False

@axon_node(category="AI/ML", version="2.3.0", node_label="Anomaly Detection", outputs=['Is Anomaly', 'Score'])
def AnomalyDetectionNode(X_List: list = [], Predict_X: float = 0.0, Contamination: float = 0.1, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Identifies outliers or unusual data points within a numerical sequence using the Isolation Forest algorithm.
Useful for fraud detection, fault monitoring, and data cleaning.

Inputs:
- Flow: Trigger execution and model training.
- X List: A list of numerical values used to train the Isolation Forest model (requires at least 5 points).
- Predict X: The specific value to be tested for anomaly status.
- Contamination: The expected proportion of outliers in the data set (range: 0.0 to 0.5, default: 0.1).

Outputs:
- Flow: Triggered after detection is complete.
- Is Anomaly: True if the Predict X value is determined to be an outlier.
- Score: The anomaly score (lower values indicate more abnormal data)."""
    data = kwargs.get('X List') or _node.properties.get('X List', [])
    new_val = kwargs.get('Predict X') if kwargs.get('Predict X') is not None else _node.properties.get('Predict X', 0.0)
    contamination = kwargs.get('Contamination') if kwargs.get('Contamination') is not None else _node.properties.get('Contamination', 0.1)
    if not ensure_sklearn():
        _node.logger.error('scikit-learn not installed.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return
    else:
        pass
    contamination = float(contamination)
    if not data or len(data) < 5:
        _node.logger.warning('Need at least 5 data points for training.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return
    else:
        pass
    if new_val is None:
        _node.logger.error('Missing Predict X.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return
    else:
        pass
    try:
        X_train = np.array(data).reshape(-1, 1)
        X_test = np.array([[float(new_val)]])
        clf = IsolationForest(contamination=contamination, random_state=42)
        clf.fit(X_train)
        pred = clf.predict(X_test)[0]
        score = clf.decision_function(X_test)[0]
        is_anomaly = pred == -1
        if is_anomaly:
            _node.logger.info(f'🚨 Anomaly Detected! Value: {new_val} (Score: {score:.2f})')
        else:
            _node.logger.info(f'Value {new_val} is Normal.')
    except Exception as e:
        _node.logger.error(f'ML Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Is Anomaly': bool(is_anomaly), 'Score': float(score)}


@axon_node(category="AI/ML", version="2.3.0", node_label="Linear Regression", outputs=['Predicted Y'])
def LinearRegressionNode(X_List: list = [], Y_List: list = [], Predict_X: float = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs simple linear regression to predict a numerical value based on historical X-Y pairs.
Ideal for trend estimation and simple forecasting.

Inputs:
- Flow: Trigger the training and prediction process.
- X List: List of independent variable values (training features).
- Y List: List of dependent variable values (training targets).
- Predict X: The value for which to predict a corresponding Y.

Outputs:
- Flow: Triggered after prediction is complete.
- Predicted Y: The estimated value calculated by the linear model."""
    x_list = kwargs.get('X List') or _node.properties.get('X List', [])
    y_list = kwargs.get('Y List') or _node.properties.get('Y List', [])
    pred_x = kwargs.get('Predict X') or _node.properties.get('Predict X', 0.0)
    if not ensure_sklearn():
        _node.logger.error('scikit-learn not installed.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return
    else:
        pass
    if not x_list or not y_list or len(x_list) != len(y_list):
        _node.logger.error('Invalid training data (X, Y must be same length lists).')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return
    else:
        pass
    if pred_x is None:
        _node.logger.error('Missing Predict X.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return
    else:
        pass
    try:
        X = np.array(x_list).reshape(-1, 1)
        y = np.array(y_list)
        model = LinearRegression()
        model.fit(X, y)
        X_new = np.array([[float(pred_x)]])
        y_pred = model.predict(X_new)[0]
        _node.logger.info(f'Prediction: X={pred_x} -> Y={y_pred:.2f}')
    except Exception as e:
        _node.logger.error(f'Regression Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return float(y_pred)
