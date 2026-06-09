from fastapi import APIRouter, Depends
from core.dependencies import require_role, get_db
from core.enums import Role
from modules.sensors.repository import SensorRepository
from modules.classifier.schemas import ClassifierRequest, ClassifierResponse
from modules.classifier.decision_tree import HazardClassifier

router = APIRouter()

@router.post("/evaluate", response_model=ClassifierResponse)
def evaluate_tree(
    req: ClassifierRequest,
    current_user = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER)),
    db = Depends(get_db)
):
    from modules.sensors.repository import get_sensor_repository
    sensor_repo = get_sensor_repository(db)
    
    # We will pass specific threshold keys. In a real system, we might look up global configs.
    gas_crit = 400.0
    temp_crit = 50.0
    light_crit = 1000.0
    
    # If the user has configured global/lab thresholds, we could override:
    thresholds = sensor_repo.get_thresholds(lab_id=None) # Or use a specific lab if we want
    for t in thresholds:
        if t.sensor_type.value == "gas" and t.critical_value:
            gas_crit = t.critical_value
        if t.sensor_type.value == "temperature" and t.critical_value:
            temp_crit = t.critical_value
        if t.sensor_type.value == "light" and t.critical_value:
            light_crit = t.critical_value

    admin_thresholds = {
        "gas_critical": gas_crit,
        "gas_warning": gas_crit * 0.8,
        "temperature_critical": temp_crit,
        "temperature_warning": temp_crit * 0.8,
        "light_critical": light_crit,
        "light_warning": light_crit * 0.8
    }

    import traceback
    try:
        classifier = HazardClassifier()
        classification, path = classifier.classify(req.sensor_data, admin_thresholds)
        
        return ClassifierResponse(classification=classification, path_taken=path)
    except Exception as e:
        from fastapi import HTTPException
        err = traceback.format_exc()
        print(err)
        raise HTTPException(status_code=500, detail=err)
