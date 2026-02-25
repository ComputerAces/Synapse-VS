"""
Data Science Nodes (Local ML).

Anomaly Detection: Isolation Forest (sklearn).
Linear Regression: Simple Prediction (sklearn).

Dependencies (Lazy): scikit-learn (sklearn), numpy.
"""
import numpy as np
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Globals
IsolationForest = None
LinearRegression = None

def ensure_sklearn():
    global IsolationForest, LinearRegression
    if IsolationForest: return True
    if DependencyManager.ensure("scikit-learn", "sklearn"):
        from sklearn.ensemble import IsolationForest as _IF
        from sklearn.linear_model import LinearRegression as _LR
        IsolationForest = _IF; LinearRegression = _LR; return True
    return False


@NodeRegistry.register("Anomaly Detection", "AI/ML")
class AnomalyDetectionNode(SuperNode):
    """
    Identifies outliers or unusual data points within a numerical sequence using the Isolation Forest algorithm.
    Useful for fraud detection, fault monitoring, and data cleaning.
    
    Inputs:
    - Flow: Trigger execution and model training.
    - X List: A list of numerical values used to train the Isolation Forest model (requires at least 5 points).
    - Predict X: The specific value to be tested for anomaly status.
    - Contamination: The expected proportion of outliers in the data set (range: 0.0 to 0.5, default: 0.1).
    
    Outputs:
    - Flow: Triggered after detection is complete.
    - Is Anomaly: True if the Predict X value is determined to be an outlier.
    - Score: The anomaly score (lower values indicate more abnormal data).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Contamination"] = 0.1
        self.properties["X List"] = []
        self.properties["Predict X"] = 0.0
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.detect_anomaly)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "X List": DataType.LIST,
            "Predict X": DataType.NUMBER,
            "Contamination": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Is Anomaly": DataType.BOOLEAN,
            "Score": DataType.NUMBER
        }

    def detect_anomaly(self, **kwargs):
        # Fallback standard
        data = kwargs.get("X List") or self.properties.get("X List", [])
        new_val = kwargs.get("Predict X") if kwargs.get("Predict X") is not None else self.properties.get("Predict X", 0.0)
        contamination = kwargs.get("Contamination") if kwargs.get("Contamination") is not None else self.properties.get("Contamination", 0.1)
        
        if not ensure_sklearn():
            self.logger.error("scikit-learn not installed.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return

        contamination = float(contamination)

        if not data or len(data) < 5:
            self.logger.warning("Need at least 5 data points for training.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return
            
        if new_val is None:
            self.logger.error("Missing Predict X.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return

        try:
            # Prepare data
            X_train = np.array(data).reshape(-1, 1)
            X_test = np.array([[float(new_val)]])
            
            # Train model
            clf = IsolationForest(contamination=contamination, random_state=42)
            clf.fit(X_train)
            
            # Predict (-1 = anomaly, 1 = normal)
            pred = clf.predict(X_test)[0]
            # Decision function (lower = more abnormal)
            score = clf.decision_function(X_test)[0]
            
            is_anomaly = (pred == -1)
            
            self.bridge.set(f"{self.node_id}_Is Anomaly", bool(is_anomaly), self.name)
            self.bridge.set(f"{self.node_id}_Score", float(score), self.name)
            
            if is_anomaly:
                self.logger.info(f"🚨 Anomaly Detected! Value: {new_val} (Score: {score:.2f})")
            else:
                self.logger.info(f"Value {new_val} is Normal.")

        except Exception as e:
            self.logger.error(f"ML Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Linear Regression", "AI/ML")
class LinearRegressionNode(SuperNode):
    """
    Performs simple linear regression to predict a numerical value based on historical X-Y pairs.
    Ideal for trend estimation and simple forecasting.
    
    Inputs:
    - Flow: Trigger the training and prediction process.
    - X List: List of independent variable values (training features).
    - Y List: List of dependent variable values (training targets).
    - Predict X: The value for which to predict a corresponding Y.
    
    Outputs:
    - Flow: Triggered after prediction is complete.
    - Predicted Y: The estimated value calculated by the linear model.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["X List"] = []
        self.properties["Y List"] = []
        self.properties["Predict X"] = 0.0
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.predict_regression)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "X List": DataType.LIST,
            "Y List": DataType.LIST,
            "Predict X": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Predicted Y": DataType.NUMBER
        }

    def predict_regression(self, **kwargs):
        # Fallback standard
        x_list = kwargs.get("X List") or self.properties.get("X List", [])
        y_list = kwargs.get("Y List") or self.properties.get("Y List", [])
        pred_x = kwargs.get("Predict X") or self.properties.get("Predict X", 0.0)
        
        if not ensure_sklearn():
            self.logger.error("scikit-learn not installed.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return

        if not x_list or not y_list or len(x_list) != len(y_list):
            self.logger.error("Invalid training data (X, Y must be same length lists).")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return

        if pred_x is None:
            self.logger.error("Missing Predict X.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return

        try:
            X = np.array(x_list).reshape(-1, 1)
            y = np.array(y_list)
            
            model = LinearRegression()
            model.fit(X, y)
            
            X_new = np.array([[float(pred_x)]])
            y_pred = model.predict(X_new)[0]
            
            self.bridge.set(f"{self.node_id}_Predicted Y", float(y_pred), self.name)
            self.logger.info(f"Prediction: X={pred_x} -> Y={y_pred:.2f}")

        except Exception as e:
            self.logger.error(f"Regression Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
