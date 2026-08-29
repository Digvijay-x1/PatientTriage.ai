"""
PatientTriage.ai - Vital Interpreter

Age-aware vital sign interpretation.

Features:
- Respiratory rate
- Heart rate
- SpO2
- Systolic blood pressure
- Diastolic blood pressure
- Temperature
- Pain score
- Pediatric BP screening using age + sex
- Backward-compatible gender parameter

IMPORTANT:
This is a prototype triage-support component.
It does not diagnose disease or replace clinical judgment.
"""


import json
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional


# ============================================================================
# RESULT STRUCTURE
# ============================================================================

@dataclass
class VitalResult:
    vital_name: str
    value: float
    status: str          # "normal", "urgent", "critical", "unknown"
    flag: bool
    reasoning: str


# ============================================================================
# VITAL INTERPRETER
# ============================================================================

class VitalInterpreter:

    """
    Age-aware vital sign interpretation.

    General vitals:
        Thresholds are loaded from vitals_thresholds.json.

    Pediatric blood pressure:
        Uses the separate age- and sex-specific
        AAP 2017 simplified screening pathway
        for children aged 1-12.

    Canonical demographic field:
        sex

    Backward compatibility:
        gender may still be supplied as an alias for sex.
    """

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def __init__(self, thresholds_path: str = "vitals_thresholds.json"):
        """Load vital thresholds from JSON."""

        with open(thresholds_path, "r", encoding="utf-8") as f:
            self.thresholds = json.load(f)

    # ========================================================================
    # AGE
    # ========================================================================

    def get_age_group(self, age: int) -> str:
        """Determine age group."""

        if age < 0:
            raise ValueError("Age cannot be negative.")

        if age < 13:
            return "pediatric"

        elif age < 65:
            return "adult"

        else:
            return "geriatric"

    # ========================================================================
    # SEX NORMALIZATION
    # ========================================================================

    def normalize_sex(self, sex: Optional[str]) -> Optional[str]:
        """
        Normalize sex input.

        Accepted:
            male, m, boy
            female, f, girl

        Returns:
            "male"
            "female"
            None
        """

        if sex is None:
            return None

        sex = str(sex).lower().strip()

        if sex in ("m", "male", "boy"):
            return "male"

        if sex in ("f", "female", "girl"):
            return "female"

        raise ValueError(
            "sex must be 'male' or 'female'."
        )

    # ========================================================================
    # RANGE PARSING
    # ========================================================================

    def parse_range(self, range_str: str):
        """
        Parse a threshold string.

        Supported formats:

            "90-120"
            "<94"
            ">30"
            ">=30"
            "<=30"
            ">160 or <70"

        Returns a structure that can be checked safely.
        """

        range_str = str(range_str).strip()

        # Handle OR conditions
        if " or " in range_str:

            parts = range_str.split(" or ")

            if len(parts) != 2:
                raise ValueError(
                    f"Invalid threshold format: {range_str}"
                )

            first = self._parse_single(parts[0])
            second = self._parse_single(parts[1])

            return ("OR", first, second)

        return ("SINGLE", self._parse_single(range_str))

    # ------------------------------------------------------------------------
    # Parse one threshold
    # ------------------------------------------------------------------------

    def _parse_single(self, s: str) -> Tuple[str, float, float]:
        """
        Parse one threshold.

        Returns:

            ("LT", value, value)
            ("LTE", value, value)
            ("GT", value, value)
            ("GTE", value, value)
            ("RANGE", lower, upper)
            ("EXACT", value, value)
        """

        s = str(s).strip()

        # Remove units and encoding artifacts
        s = s.replace("%", "")
        s = s.replace("°C", "")
        s = s.replace("Â°C", "")
        s = s.replace("Â", "")
        s = s.replace("ºC", "")
        s = s.strip()

        # >=
        if s.startswith(">="):

            value = float(s[2:].strip())

            return ("GTE", value, value)

        # <=
        if s.startswith("<="):

            value = float(s[2:].strip())

            return ("LTE", value, value)

        # >
        if s.startswith(">"):

            value = float(s[1:].strip())

            return ("GT", value, value)

        # <
        if s.startswith("<"):

            value = float(s[1:].strip())

            return ("LT", value, value)

        # Range
        if "-" in s:

            parts = s.split("-")

            if len(parts) != 2:
                raise ValueError(
                    f"Invalid range format: {s}"
                )

            lower = float(parts[0].strip())
            upper = float(parts[1].strip())

            return ("RANGE", lower, upper)

        # Exact value
        value = float(s)

        return ("EXACT", value, value)

    # ========================================================================
    # RANGE MATCHING
    # ========================================================================

    def value_matches_range(
        self,
        value: float,
        range_str: str
    ) -> bool:

        """
        Determine whether a value falls inside a threshold.

        Examples:

            "<94"
            ">30"
            ">=30"
            "<=30"
            "90-120"
            ">160 or <70"
        """

        parsed = self.parse_range(range_str)

        # ------------------------------------------------------------
        # SINGLE
        # ------------------------------------------------------------

        if parsed[0] == "SINGLE":

            operator, lower, upper = parsed[1]

            if operator == "LT":
                return value < lower

            if operator == "LTE":
                return value <= lower

            if operator == "GT":
                return value > lower

            if operator == "GTE":
                return value >= lower

            if operator == "RANGE":
                return lower <= value <= upper

            if operator == "EXACT":
                return value == lower

        # ------------------------------------------------------------
        # OR
        # ------------------------------------------------------------

        elif parsed[0] == "OR":

            _, first, second = parsed

            return (
                self._matches_parsed_value(value, first)
                or
                self._matches_parsed_value(value, second)
            )

        return False

    # ------------------------------------------------------------------------
    # Check parsed condition
    # ------------------------------------------------------------------------

    def _matches_parsed_value(
        self,
        value: float,
        parsed
    ) -> bool:

        operator, lower, upper = parsed

        if operator == "LT":
            return value < lower

        if operator == "LTE":
            return value <= lower

        if operator == "GT":
            return value > lower

        if operator == "GTE":
            return value >= lower

        if operator == "RANGE":
            return lower <= value <= upper

        if operator == "EXACT":
            return value == lower

        return False

    # ========================================================================
    # PEDIATRIC BLOOD PRESSURE
    # ========================================================================

    def interpret_pediatric_bp(
        self,
        systolic_bp: float,
        diastolic_bp: float,
        age: int,
        sex: Optional[str] = None,
        gender: Optional[str] = None
    ) -> Dict:

        """
        Interpret pediatric blood pressure using the
        age- and sex-specific screening table.

        Applicable to children aged 1-12.

        IMPORTANT:
        This is a SCREENING tool.

        The screening thresholds identify measurements
        requiring further evaluation. They do not diagnose
        hypertension.

        Parameters:
            systolic_bp:
                Systolic BP in mmHg.

            diastolic_bp:
                Diastolic BP in mmHg.

            age:
                Age in years.

            sex:
                "male" / "female"

            gender:
                Backward-compatible alias for sex.
        """

        # ------------------------------------------------------------
        # Normalize sex / gender
        # ------------------------------------------------------------

        if sex is None and gender is not None:
            sex = gender

        sex = self.normalize_sex(sex)

        # ------------------------------------------------------------
        # Validate age
        # ------------------------------------------------------------

        if age < 1 or age >= 13:
            raise ValueError(
                "Pediatric AAP BP screening is implemented "
                "for ages 1-12."
            )

        if sex is None:
            raise ValueError(
                "Pediatric BP requires sex."
            )

        # ------------------------------------------------------------
        # Validate BP values
        # ------------------------------------------------------------

        if systolic_bp <= 0:
            raise ValueError(
                "Systolic BP must be greater than 0."
            )

        if diastolic_bp <= 0:
            raise ValueError(
                "Diastolic BP must be greater than 0."
            )

        # ------------------------------------------------------------
        # Get AAP table
        # ------------------------------------------------------------

        pediatric_thresholds = self.thresholds["pediatric"]

        if "blood_pressure_screening" not in pediatric_thresholds:
            raise ValueError(
                "Pediatric BP screening table is missing "
                "from the JSON file."
            )

        bp_table = (
            pediatric_thresholds[
                "blood_pressure_screening"
            ]["thresholds"]
        )

        # ------------------------------------------------------------
        # Age-specific threshold
        # ------------------------------------------------------------

        age_key = str(age)

        if sex not in bp_table:
            raise ValueError(
                f"No pediatric BP table available for sex '{sex}'."
            )

        if age_key not in bp_table[sex]:
            raise ValueError(
                f"No pediatric BP threshold available "
                f"for age {age}."
            )

        screening = bp_table[sex][age_key]

        screening_sbp = screening["systolic_bp"]
        screening_dbp = screening["diastolic_bp"]

        # ------------------------------------------------------------
        # Compare SBP and DBP
        # ------------------------------------------------------------

        systolic_flag = systolic_bp >= screening_sbp

        diastolic_flag = diastolic_bp >= screening_dbp

        overall_flag = (
            systolic_flag or diastolic_flag
        )

        # ------------------------------------------------------------
        # Status
        # ------------------------------------------------------------

        if overall_flag:
            status = "urgent"
        else:
            status = "normal"

        # ------------------------------------------------------------
        # AAP screening result
        # ------------------------------------------------------------

        if overall_flag:

            aap_result = (
                "BP requires further evaluation "
                "according to the pediatric screening threshold."
            )

        else:

            aap_result = (
                "BP is below the pediatric screening threshold."
            )

        # ------------------------------------------------------------
        # Reasoning
        # ------------------------------------------------------------

        reasons = []

        if systolic_flag:

            reasons.append(
                f"SBP {systolic_bp} mmHg >= "
                f"screening threshold {screening_sbp} mmHg"
            )

        if diastolic_flag:

            reasons.append(
                f"DBP {diastolic_bp} mmHg >= "
                f"screening threshold {screening_dbp} mmHg"
            )

        if reasons:

            reasoning = (
                "Pediatric BP screening flag: "
                + "; ".join(reasons)
                + ". Further evaluation is recommended."
            )

        else:

            reasoning = (
                f"Pediatric BP is below the screening "
                f"threshold for a {age}-year-old {sex}."
            )

        # ------------------------------------------------------------
        # Return
        # ------------------------------------------------------------

        return {
            "vital_name": "pediatric_blood_pressure",

            "systolic_bp": systolic_bp,

            "diastolic_bp": diastolic_bp,

            "age": age,

            "sex": sex,

            "systolic_flag": systolic_flag,

            "diastolic_flag": diastolic_flag,

            "flag": overall_flag,

            "status": status,

            "aap_screening_result": aap_result,

            "screening_sbp": screening_sbp,

            "screening_dbp": screening_dbp,

            "reasoning": reasoning
        }

    # ========================================================================
    # GENERAL VITAL INTERPRETER
    # ========================================================================

    def interpret_vital(
        self,
        vital_name: str,
        value: float,
        age: int,
        sex: Optional[str] = None,
        gender: Optional[str] = None
    ) -> VitalResult:

        """
        Interpret one non-pediatric-BP vital.

        Pediatric BP must go through
        interpret_pediatric_bp().
        """

        # ------------------------------------------------------------
        # Normalize sex / gender
        # ------------------------------------------------------------

        if sex is None and gender is not None:
            sex = gender

        sex = self.normalize_sex(sex)

        # ------------------------------------------------------------
        # Validate value
        # ------------------------------------------------------------

        if value is None:
            raise ValueError(
                f"{vital_name} cannot be None."
            )

        try:
            value = float(value)

        except (TypeError, ValueError):
            raise ValueError(
                f"{vital_name} must be numeric."
            )

        # ------------------------------------------------------------
        # Pain validation
        # ------------------------------------------------------------

        if vital_name == "pain":

            if value < 0 or value > 10:
                raise ValueError(
                    "Pain score must be between 0 and 10."
                )

        # ------------------------------------------------------------
        # Age group
        # ------------------------------------------------------------

        age_group = self.get_age_group(age)

        # ------------------------------------------------------------
        # Pediatric BP protection
        # ------------------------------------------------------------

        if (
            age_group == "pediatric"
            and vital_name in (
                "systolic_bp",
                "diastolic_bp"
            )
        ):

            raise ValueError(
                "Pediatric BP must be interpreted using "
                "interpret_pediatric_bp(), because pediatric "
                "BP requires both SBP/DBP and sex."
            )

        # ------------------------------------------------------------
        # Get age-specific thresholds
        # ------------------------------------------------------------

        age_thresholds = self.thresholds[age_group]

        ranges = (
            age_thresholds[
                "normal_ranges"
            ].get(vital_name, {})
        )

        # ------------------------------------------------------------
        # Unknown vital
        # ------------------------------------------------------------

        if not ranges:

            return VitalResult(
                vital_name=vital_name,
                value=value,
                status="unknown",
                flag=False,
                reasoning=(
                    f"{vital_name} is not defined "
                    f"in the threshold configuration."
                )
            )

        # ------------------------------------------------------------
        # Critical first
        # ------------------------------------------------------------

        status = "normal"

        if "critical" in ranges:

            if self.value_matches_range(
                value,
                ranges["critical"]
            ):

                status = "critical"

        # ------------------------------------------------------------
        # Urgent second
        # ------------------------------------------------------------

        if (
            status != "critical"
            and "urgent" in ranges
        ):

            if self.value_matches_range(
                value,
                ranges["urgent"]
            ):

                status = "urgent"

        # ------------------------------------------------------------
        # Flag
        # ------------------------------------------------------------

        flag = status != "normal"

        # ------------------------------------------------------------
        # Reasoning
        # ------------------------------------------------------------

        reasoning = (
            f"{vital_name}={value} is {status} "
            f"for {age_group} (age {age})"
        )

        # ------------------------------------------------------------
        # Return
        # ------------------------------------------------------------

        return VitalResult(
            vital_name=vital_name,
            value=value,
            status=status,
            flag=flag,
            reasoning=reasoning
        )

    # ========================================================================
    # CHECK ALL VITALS
    # ========================================================================

    def check_all_vitals(
        self,
        vitals_dict: Dict[str, float],
        age: int,
        sex: Optional[str] = None,
        gender: Optional[str] = None
    ) -> Tuple[int, int, List[str], List]:

        """
        Interpret all supplied vitals.

        Parameters:

            vitals_dict:
                Dictionary such as:

                {
                    "systolic_bp": 125,
                    "diastolic_bp": 80,
                    "spo2": 98,
                    "heart_rate": 75,
                    "respiratory_rate": 16,
                    "temperature": 36.8,
                    "pain": 2
                }

            age:
                Patient age.

            sex:
                Canonical demographic field.

            gender:
                Backward-compatible alias for sex.

        Returns:

            (
                number_of_critical_flags,
                number_of_urgent_flags,
                reasoning_list,
                all_results
            )
        """

        # ------------------------------------------------------------
        # Basic validation
        # ------------------------------------------------------------

        if not isinstance(vitals_dict, dict):
            raise ValueError(
                "vitals_dict must be a dictionary."
            )

        # ------------------------------------------------------------
        # Normalize sex / gender
        # ------------------------------------------------------------

        if sex is None and gender is not None:
            sex = gender

        sex = self.normalize_sex(sex)

        # ------------------------------------------------------------
        # Counters
        # ------------------------------------------------------------

        critical_count = 0
        urgent_count = 0

        vital_results = []

        # ====================================================================
        # PEDIATRIC BP PATH
        # ====================================================================

        has_sbp = "systolic_bp" in vitals_dict
        has_dbp = "diastolic_bp" in vitals_dict

        if age < 13 and (has_sbp or has_dbp):

            # ------------------------------------------------------------
            # Both SBP and DBP required
            # ------------------------------------------------------------

            if not has_sbp or not has_dbp:

                raise ValueError(
                    "Pediatric BP requires both "
                    "systolic_bp and diastolic_bp."
                )

            # ------------------------------------------------------------
            # Sex required
            # ------------------------------------------------------------

            if sex is None:

                raise ValueError(
                    "Pediatric BP requires sex."
                )

            # ------------------------------------------------------------
            # Interpret pediatric BP
            # ------------------------------------------------------------

            bp_result = self.interpret_pediatric_bp(
                systolic_bp=vitals_dict["systolic_bp"],
                diastolic_bp=vitals_dict["diastolic_bp"],
                age=age,
                sex=sex
            )

            vital_results.append(bp_result)

            # ------------------------------------------------------------
            # Count BP flag
            # ------------------------------------------------------------

            if bp_result["status"] == "critical":

                critical_count += 1

            elif bp_result["status"] == "urgent":

                urgent_count += 1

        # ====================================================================
        # GENERAL VITALS
        # ====================================================================

        for vital_name, value in vitals_dict.items():

            # ------------------------------------------------------------
            # Pediatric BP already handled above
            # ------------------------------------------------------------

            if (
                age < 13
                and vital_name in (
                    "systolic_bp",
                    "diastolic_bp"
                )
            ):
                continue

            # ------------------------------------------------------------
            # Interpret normal vital
            # ------------------------------------------------------------

            result = self.interpret_vital(
                vital_name=vital_name,
                value=value,
                age=age,
                sex=sex
            )

            vital_results.append(result)

            # ------------------------------------------------------------
            # Count flags
            # ------------------------------------------------------------

            if result.status == "critical":

                critical_count += 1

            elif result.status == "urgent":

                urgent_count += 1

        # ====================================================================
        # REASONING
        # ====================================================================

        reasoning = []

        for result in vital_results:

            if isinstance(result, VitalResult):

                if result.flag:
                    reasoning.append(result.reasoning)

            else:

                if result["flag"]:
                    reasoning.append(result["reasoning"])

        # ====================================================================
        # RETURN
        # ====================================================================

        return (
            critical_count,
            urgent_count,
            reasoning,
            vital_results
        )


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":

    interpreter = VitalInterpreter()

    print("=" * 70)
    print("VITAL INTERPRETER TEST CASES")
    print("=" * 70)

    # ========================================================================
    # TEST 1: ADULT
    # ========================================================================

    print(
        "\n[TEST 1] Adult - normal vitals"
    )

    vitals_1 = {
        "spo2": 97,
        "heart_rate": 78,
        "systolic_bp": 125,
        "diastolic_bp": 80,
        "respiratory_rate": 16,
        "temperature": 36.8,
        "pain": 2
    }

    critical, urgent, reasoning, results = (
        interpreter.check_all_vitals(
            vitals_1,
            age=45,
            sex="male"
        )
    )

    print(f"Critical flags: {critical}")
    print(f"Urgent flags: {urgent}")

    for r in results:
        print(f"  - {r.reasoning}")

    # ========================================================================
    # TEST 2: ADULT WITH HIGH SBP + PAIN
    # ========================================================================

    print(
        "\n[TEST 2] Adult - high SBP + severe pain"
    )

    vitals_2 = {
        "spo2": 98,
        "heart_rate": 90,
        "systolic_bp": 175,
        "diastolic_bp": 105,
        "respiratory_rate": 18,
        "temperature": 37.0,
        "pain": 8
    }

    critical, urgent, reasoning, results = (
        interpreter.check_all_vitals(
            vitals_2,
            age=35,
            sex="female"
        )
    )

    print(f"Critical flags: {critical}")
    print(f"Urgent flags: {urgent}")

    for r in results:
        print(f"  - {r.reasoning}")

    # ========================================================================
    # TEST 3: ADULT CRITICAL VITALS
    # ========================================================================

    print(
        "\n[TEST 3] Adult - critical vitals"
    )

    vitals_3 = {
        "spo2": 88,
        "heart_rate": 140,
        "systolic_bp": 190,
        "diastolic_bp": 125,
        "respiratory_rate": 32,
        "temperature": 40.0,
        "pain": 9
    }

    critical, urgent, reasoning, results = (
        interpreter.check_all_vitals(
            vitals_3,
            age=52,
            sex="male"
        )
    )

    print(f"Critical flags: {critical}")
    print(f"Urgent flags: {urgent}")

    for r in results:
        print(f"  - {r.reasoning}")

    # ========================================================================
    # TEST 4: GERIATRIC
    # ========================================================================

    print(
        "\n[TEST 4] Geriatric"
    )

    vitals_4 = {
        "spo2": 93,
        "heart_rate": 106,
        "systolic_bp": 165,
        "diastolic_bp": 105,
        "respiratory_rate": 28,
        "temperature": 38.2,
        "pain": 6
    }

    critical, urgent, reasoning, results = (
        interpreter.check_all_vitals(
            vitals_4,
            age=78,
            sex="female"
        )
    )

    print(f"Critical flags: {critical}")
    print(f"Urgent flags: {urgent}")

    for r in results:
        print(f"  - {r.reasoning}")

    # ========================================================================
    # TEST 5: PEDIATRIC
    # ========================================================================

    print(
        "\n[TEST 5] Pediatric - 8yo male with BP"
    )

    vitals_5 = {
        "systolic_bp": 112,
        "diastolic_bp": 70,
        "spo2": 98,
        "heart_rate": 90,
        "respiratory_rate": 28,
        "temperature": 37.0,
        "pain": 2
    }

    critical, urgent, reasoning, results = (
        interpreter.check_all_vitals(
            vitals_5,
            age=8,
            sex="male"
        )
    )

    print(f"Critical flags: {critical}")
    print(f"Urgent flags: {urgent}")

    for r in results:

        if isinstance(r, dict):

            print(f"  - {r['reasoning']}")

            if r["vital_name"] == "pediatric_blood_pressure":

                print(
                    f"    SBP flag: {r['systolic_flag']}"
                )

                print(
                    f"    DBP flag: {r['diastolic_flag']}"
                )

                print(
                    f"    AAP result: "
                    f"{r['aap_screening_result']}"
                )

        else:

            print(f"  - {r.reasoning}")

    # ========================================================================
    # TEST 6: SEX ALIAS
    # ========================================================================

    print(
        "\n[TEST 6] Pediatric - using gender alias"
    )

    vitals_6 = {
        "systolic_bp": 100,
        "diastolic_bp": 60,
        "pain": 3
    }

    critical, urgent, reasoning, results = (
        interpreter.check_all_vitals(
            vitals_6,
            age=4,
            gender="female"
        )
    )

    print(f"Critical flags: {critical}")
    print(f"Urgent flags: {urgent}")

    for r in results:

        if isinstance(r, dict):
            print(f"  - {r['reasoning']}")

        else:
            print(f"  - {r.reasoning}")

    print("\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)