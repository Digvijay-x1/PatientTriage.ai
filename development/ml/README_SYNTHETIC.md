# PatientTriage.ai - Synthetic Prototype Build

This package is configured to run the ESI prototype with a synthetic demonstration dataset.

## ML inputs
- temperature
- heartrate
- resprate
- o2sat
- sbp
- dbp
- pain
- gender
- chiefcomplaint

The ML model supports ESI 1, 2, and 3 only.

The age-aware VitalInterpreter and Safety Engine remain separate from the ML model and continue to use the patient's actual age and sex, including pediatric BP screening.

## Run

```powershell
py test_integrated.py
```

To retrain the model from the included synthetic dataset:

```powershell
py train_integrated_esi_model.py
```

## Important

`esi_training_data.csv` in this package is SYNTHETIC and is for prototype/demo purposes only. It is not MIMIC-IV data and the resulting accuracy/confidence must not be presented as clinical validation.
