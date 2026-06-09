from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class TreeNode:
    def __init__(self, name: str, attribute: str = None, operator: str = None, 
                 threshold_key: str = None, static_threshold: float = None,
                 left: 'TreeNode' = None, right: 'TreeNode' = None, 
                 is_leaf: bool = False, classification: str = None):
        self.name = name
        self.attribute = attribute          # e.g., 'gas_level'
        self.operator = operator            # '>', '<', '>=', '<='
        self.threshold_key = threshold_key  # key to look up in admin thresholds (e.g. 'gas_critical')
        self.static_threshold = static_threshold # fallback if no key
        self.left = left                    # True branch
        self.right = right                  # False branch
        self.is_leaf = is_leaf
        self.classification = classification # e.g. 'Safe', 'Warning', 'Critical'

    def evaluate(self, data: Dict[str, float], thresholds: Dict[str, float], path: List[str]):
        if self.is_leaf:
            path.append(f"Reached Leaf: {self.name}")
            return self.classification, path

        val = data.get(self.attribute)
        if val is None:
            # Missing data, default to False branch or handle gracefully
            path.append(f"Missing {self.attribute}, branching False.")
            return self.right.evaluate(data, thresholds, path)

        thresh = thresholds.get(self.threshold_key, self.static_threshold)
        if thresh is None:
            # Fallback
            thresh = 0.0

        condition_met = False
        if self.operator == '>':
            condition_met = val > thresh
        elif self.operator == '>=':
            condition_met = val >= thresh
        elif self.operator == '<':
            condition_met = val < thresh
        elif self.operator == '<=':
            condition_met = val <= thresh

        if condition_met:
            path.append(f"[{self.name}] {self.attribute} ({val}) {self.operator} {thresh} -> TRUE")
            return self.left.evaluate(data, thresholds, path)
        else:
            path.append(f"[{self.name}] {self.attribute} ({val}) {self.operator} {thresh} -> FALSE")
            return self.right.evaluate(data, thresholds, path)

class HazardClassifier:
    def __init__(self):
        self.root = self._build_tree()

    def _build_tree(self) -> TreeNode:
        # Build the hand-crafted expert system decision tree
        
        # Leaves
        leaf_safe = TreeNode("Safe Leaf", is_leaf=True, classification="Safe")
        leaf_warning = TreeNode("Warning Leaf", is_leaf=True, classification="Warning")
        leaf_high_risk = TreeNode("High Risk Leaf", is_leaf=True, classification="High Risk")
        leaf_critical = TreeNode("Critical Leaf", is_leaf=True, classification="Critical")

        # Light Check for light-sensitive chemicals (checked if temp is high)
        check_light = TreeNode(
            name="Light Exposure Check",
            attribute="light_level",
            operator=">",
            threshold_key="light_warning",
            static_threshold=800.0,
            left=TreeNode("Photochemical Reaction Leaf", is_leaf=True, classification="Critical"), # High light + Heat + Gas = Photochemical hazard
            right=leaf_high_risk # High Gas + High Temp = High Risk (even if no explosion hazard)
        )

        # Humidity Check (Secondary check if vibration is normal but gas and temp are high)
        check_hum = TreeNode(
            name="Humidity Check",
            attribute="humidity",
            operator=">",
            static_threshold=80.0,
            left=TreeNode("Evacuation Leaf", is_leaf=True, classification="Critical"), # Swamp gas explosion risk
            right=check_light # If humidity is fine, check if light is triggering a photochemical reaction
        )

        # Vibration Check
        check_vib = TreeNode(
            name="Vibration Check",
            attribute="vibration_level",
            operator=">",
            static_threshold=2.0, # standard warning
            left=leaf_critical,
            right=check_hum # If vibration is normal, check humidity
        )

        # Temp Check
        check_temp = TreeNode(
            name="Temperature Check",
            attribute="temperature",
            operator=">",
            threshold_key="temperature_warning",
            static_threshold=40.0, # Using dynamic warning threshold
            left=check_vib, # Temp is high, check vibration
            right=leaf_warning # Gas high, Temp normal -> Warning
        )

        # Independent anomaly checks when Gas is normal
        ind_vib = TreeNode(
            name="Independent Vibration Check",
            attribute="vibration_level",
            operator=">",
            static_threshold=2.0,
            left=TreeNode("Seismic Anomaly Leaf", is_leaf=True, classification="Warning"),
            right=leaf_safe
        )

        ind_temp = TreeNode(
            name="Independent Temperature Check",
            attribute="temperature",
            operator=">",
            threshold_key="temperature_warning",
            static_threshold=40.0,
            left=TreeNode("Thermal Anomaly Leaf", is_leaf=True, classification="Warning"),
            right=ind_vib
        )

        # Root: Gas Check
        root = TreeNode(
            name="Root Gas Check",
            attribute="gas_level",
            operator=">",
            threshold_key="gas_warning",
            static_threshold=320.0,
            left=check_temp, # Gas is high -> check combined hazards
            right=ind_temp  # Gas is normal -> check independent hazards
        )

        return root

    def classify(self, sensor_data: Dict[str, float], admin_thresholds: Dict[str, float]):
        path = []
        classification, path = self.root.evaluate(sensor_data, admin_thresholds, path)
        return classification, path
