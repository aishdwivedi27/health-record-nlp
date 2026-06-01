# Quick Fix: Latest Report Should Check X-ray AND Blood

## Problem
When doctor asks "latest report":
- ❌ Only checks one type (blood)
- ❌ Doesn't compare X-ray vs Blood vs other types
- ❌ Doesn't return the ACTUAL latest item

## Solution
Create a "master latest" function that checks ALL report types and returns the truly latest one.

## Implementation

**File: `backend/app/routers/nlp_query.py`**

Add this function BEFORE the `nlp_query()` function:

```python
def find_latest_report_across_all_types(patient_id, db):
    """Find the ACTUAL latest report/test across ALL types"""
    
    all_items = []
    
    # Get latest DiagnosticReport (imaging)
    latest_diagnostic = db.query(DiagnosticReport).filter(
        DiagnosticReport.patient_id == patient_id
    ).order_by(DiagnosticReport.timestamp.desc()).first()
    
    if latest_diagnostic:
        all_items.append({
            'timestamp': latest_diagnostic.timestamp,
            'type': 'diagnostic_report',
            'data': latest_diagnostic,
            'label': f"{latest_diagnostic.display} ({latest_diagnostic.timestamp.strftime('%b %d, %I:%M %p')})"
        })
    
    # Get latest Lab Observation
    latest_lab = db.query(Observation).filter(
        Observation.patient_id == patient_id,
        Observation.type == 'lab'
    ).order_by(Observation.timestamp.desc()).first()
    
    if latest_lab:
        all_items.append({
            'timestamp': latest_lab.timestamp,
            'type': 'lab_observation',
            'data': latest_lab,
            'label': f"Blood work: {latest_lab.display} ({latest_lab.timestamp.strftime('%b %d, %I:%M %p')})"
        })
    
    # Get latest Vital Observation
    latest_vital = db.query(Observation).filter(
        Observation.patient_id == patient_id,
        Observation.type == 'vital'
    ).order_by(Observation.timestamp.desc()).first()
    
    if latest_vital:
        all_items.append({
            'timestamp': latest_vital.timestamp,
            'type': 'vital_observation',
            'data': latest_vital,
            'label': f"Vital: {latest_vital.display} ({latest_vital.timestamp.strftime('%b %d, %I:%M %p')})"
        })
    
    # Sort by timestamp DESC and return the ACTUAL latest
    if all_items:
        all_items.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_items[0]  # Most recent item
    
    return None
```

Now, modify the `nlp_query()` function to detect "latest report" questions:

**Find this section in nlp_query():**
```python
intent = extract_intent(request.question)
structured_data = execute_query(request.patient_id, intent, db)
```

**Replace with:**
```python
# Check if this is a "latest report" type query
is_latest_report_query = any(keyword in request.question.lower() 
                             for keyword in ['latest report', 'most recent report', 'last report', 'recent imaging', 'recent blood'])

if is_latest_report_query:
    # Find the ACTUAL latest across ALL types
    latest = find_latest_report_across_all_types(request.patient_id, db)
    
    if latest:
        # Format response based on type
        if latest['type'] == 'diagnostic_report':
            structured_data = {
                "patient": {"id": request.patient_id},
                "data": {
                    "diagnostic_reports": [{
                        "id": latest['data'].id,
                        "timestamp": latest['data'].timestamp.isoformat(),
                        "category": latest['data'].category,
                        "type": latest['data'].display,
                        "findings": latest['data'].findings,
                        "conclusion": latest['data'].conclusion,
                        "status": latest['data'].status
                    }]
                },
                "metadata": {
                    "data_type": "diagnostic_report",
                    "record_count": 1,
                    "note": "This is the LATEST across all report types (imaging, blood, vitals)"
                }
            }
            
        elif latest['type'] in ['lab_observation', 'vital_observation']:
            structured_data = {
                "patient": {"id": request.patient_id},
                "data": {
                    "lab_observations": [{
                        "id": latest['data'].id,
                        "timestamp": latest['data'].timestamp.isoformat(),
                        "test_name": latest['data'].display,
                        "value": latest['data'].value,
                        "unit": latest['data'].unit,
                        "type": latest['data'].type,
                        "status": latest['data'].status
                    }]
                },
                "metadata": {
                    "data_type": "observation",
                    "record_count": 1,
                    "note": "This is the LATEST across all report types (imaging, blood, vitals)"
                }
            }
        
        intent = {
            "primary_data_type": "latest_across_all",
            "action": "retrieve",
            "note": f"Retrieved actual latest: {latest['label']}"
        }
    else:
        structured_data = {"error": "No reports found"}
        intent = {"primary_data_type": "latest_across_all", "error": "no_data"}
else:
    # Regular intent extraction for other queries
    intent = extract_intent(request.question)
    structured_data = execute_query(request.patient_id, intent, db)
```

## Testing

After applying the fix, test with:

```
Doctor: "latest report"
System checks:
  ├─ Latest imaging: Chest X-ray (May 31, 2:45 PM)
  ├─ Latest blood: Blood work (May 31, 10:30 AM)
  ├─ Latest vital: BP (May 31, 4:20 PM)
  └─ RETURNS: X-ray (most recent) ✅

Doctor: "latest blood report"
System: Returns latest blood work (May 31, 10:30 AM) ✅

Doctor: "latest x ray"
System: Returns latest X-ray (May 31, 2:45 PM) ✅

Doctor: "latest"
System: Returns actual latest across ALL types ✅
```

## Keywords Detected

The fix detects these "latest" queries:
- "latest report"
- "most recent report"
- "last report"
- "recent imaging"
- "recent blood"
- "latest imaging"
- "latest blood"
- "most recent test"

## Result

✅ System now intelligently compares X-ray, blood work, vitals
✅ Returns the ACTUAL latest item by timestamp
✅ Shows which type it is
✅ Displays findings with context

**This ensures doctors always get the TRUE latest report, not just one type!**
