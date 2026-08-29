import joblib
from pathlib import Path


MODEL_PATH = Path("esi_integrated_model.joblib")

model = joblib.load(MODEL_PATH)

print("=" * 70)
print("CHECKING SAVED MODEL FEATURES")
print("=" * 70)

print("\nMODEL TYPE:")
print(type(model))

# ------------------------------------------------------------
# Check pipeline steps
# ------------------------------------------------------------

if hasattr(model, "named_steps"):

    print("\nPIPELINE STEPS:")

    for name, step in model.named_steps.items():
        print(f"  {name}: {type(step)}")

# ------------------------------------------------------------
# Find feature names
# ------------------------------------------------------------

print("\nFEATURE INFORMATION")
print("-" * 70)

if hasattr(model, "feature_names_in_"):

    print("\nmodel.feature_names_in_:")
    for i, feature in enumerate(model.feature_names_in_):
        print(f"{i:2d}: {feature}")

elif hasattr(model, "named_steps"):

    found = False

    for name, step in model.named_steps.items():

        if hasattr(step, "feature_names_in_"):

            found = True

            print(
                f"\n{name}.feature_names_in_:"
            )

            for i, feature in enumerate(
                step.feature_names_in_
            ):
                print(f"{i:2d}: {feature}")

    if not found:
        print(
            "\nNo feature_names_in_ found in pipeline."
        )

else:

    print(
        "\nCould not find feature_names_in_."
    )

# ------------------------------------------------------------
# Number of expected features
# ------------------------------------------------------------

print("\nNUMBER OF FEATURES")

if hasattr(model, "n_features_in_"):

    print(
        "Model expects:",
        model.n_features_in_,
        "features"
    )

elif hasattr(model, "named_steps"):

    for name, step in model.named_steps.items():

        if hasattr(step, "n_features_in_"):

            print(
                f"{name} expects:",
                step.n_features_in_,
                "features"
            )

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)