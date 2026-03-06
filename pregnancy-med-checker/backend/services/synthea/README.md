# Unpack and Repack with Selected Modules

Guide for unzipping, modifying, and repacking a runnable Synthea JAR.

### **1. Download JAR and create temp directory*

Go to https://github.com/synthetichealth/synthea/wiki/Basic-Setup-and-Running and download `synthea-with-dependencies.jar`

Move directory if needed, and in the terminal navigate to directory where JAR is located.

Then, create a temporary directory and navigate to it.

```bash
mkdir tmpjar
cd tmpjar
```

### **2. Extract the JAR**

```bash
jar xf ../synthea-with-dependencies.jar
```

### **3. Edit what you want**

Example: delete all default modules:

```bash
rm -r modules/*
```

Or add your own:

```bash
cp ../my_module.json modules/
```

You can also edit them in the UI (for example in Mac, reveal in Finder)

Once the modules/ folder is ready with the selection and edited version of the original default modules, then we can repack.

### **4. Repack the JAR**

```bash
jar cfm ../synthea-with-dependencies-custom.jar META-INF/MANIFEST.MF .
```

### **5. Run it**

```bash
cd ..
java -jar synthea-with-dependencies-custom.jar
```

# Custom Synthea Modules for Pregnancy & Lactation Tracking

The my_modules/ directory contains custom Synthea modules that generate FHIR resources for pregnancy and lactation tracking.

## New Modules

### 1. `gestational_weeks.json`
**Module Name:** `Gestational_Weeks`

Tracks gestational age weekly during pregnancy.

- **Creates:** `Observation` resources
- **LOINC Code:** `11778-8` (Gestational age)
- **Trigger:** Runs when `pregnancy_active` attribute is `true`
- **Frequency:** Creates one observation per week while pregnancy is active

### 2. `pregnancy_exposures.json`
**Module Name:** `Pregnancy_Exposures`

Tracks medications and supplements taken during each trimester of pregnancy.

- **Creates:** `MedicationRequest` resources
- **Code System:** RxNorm
- **Trigger:** Runs when `pregnancy_active` attribute is `true`
- **Medications:** Includes prenatal vitamins, pain relievers, anti-nausea medications, antibiotics, and supplements
- **Trimester-based:** Different medications can be assigned per trimester (T1, T2, T3)

### 3. `lactation_status.json`
**Module Name:** `Lactation_Status`

Tracks lactation status after live birth.

- **Creates:** `Observation` resources
- **SNOMED Code:** `225747004` (Lactation status)
- **Trigger:** Runs when `live_birth` attribute is `true`
- **States:** Creates observations when lactation starts and ends

## Dependencies

These modules require attributes set by Synthea's built-in modules:

- `pregnancy_active` - Set by `pregnancy.json` when pregnancy begins
- `live_birth` - Set by `pregnancy.json` when a live birth occurs

## Usage

These modules are automatically loaded when:
- `MODULES_DIR` is set to `./my_modules` to add them on top of base modules

The modules will automatically execute when the required attributes are set by the pregnancy module.

## FHIR Resources Generated

- **Observations:** Gestational age (weekly) and lactation status
- **MedicationRequests:** Pregnancy-related medications with RxNorm codes

All resources include proper coding information (code, system, display) for integration with the FHIR ingestion pipeline.

# Modules to Use - Curated Medication-Generating Modules

This directory contains a curated subset of Synthea modules focused on generating medications for pregnancy medication safety checking. These modules were extracted from Synthea's default modules and have been modified for this project.

## Source

These modules were extracted from `synthea-with-dependencies.jar` using:

```bash
unzip -q synthea-with-dependencies.jar "modules/*.json"
```

From the full set of Synthea modules, we selected only those that:
- Generate medications (for interaction checking)
- Are relevant to pregnancy and reproductive health
- Are common conditions in reproductive-age women

## Modifications

### 1. Pregnancy Module Integration

**File:** `pregnancy.json`

Modified to integrate with custom modules in `my_modules/`:

- **After `Become_Pregnant` state:**
  - Added `Set_Pregnancy_Active` state: Sets `pregnancy_active = true` attribute
  - Added `Call_Gestational_Weeks` state: Calls `Gestational_Weeks` submodule
  - Added `Call_Pregnancy_Exposures` state: Calls `Pregnancy_Exposures` submodule

- **After `Birth` state:**
  - Added `Set_Live_Birth` state: Sets `live_birth = true` attribute
  - Added `Call_Lactation_Status` state: Calls `Lactation_Status` submodule

- **When pregnancy ends:**
  - Added `Unset_Pregnancy_Active` state: Sets `pregnancy_active = false`

These modifications ensure that custom modules in `my_modules/` are automatically called during pregnancy, generating:
- Gestational age observations (weekly)
- Pregnancy medication requests (per trimester)
- Lactation status observations (after birth)

### 2. Increased Pregnancy Frequency

To generate more pregnancies in the dataset, the following modules have been modified (stored in my_edited_modules/ for easier viewing, but must be updated in the JARs modules/):

#### `sexual_activity.json`
- **Purpose:** Increased sexual activity rates for reproductive-age women
- **Changes:** Higher percentages of sexually active women in age groups 20-40
- **Impact:** More opportunities for pregnancy

#### `contraceptives.json`
- **Purpose:** Reduced contraceptive use rates
- **Changes:** Lower distributions for effective contraceptives (pill, IUD, implant), higher "none" distribution
- **Impact:** More women without contraception = higher pregnancy probability

#### `female_reproduction.json`
- **Purpose:** Increased monthly pregnancy probability
- **Changes:** Higher pregnancy probability when no contraception is used
- **Impact:** More pregnancies per reproductive cycle

**Note:** The exact modifications depend on your requirements. See `../tmp/PREGNANCY_FREQUENCY_GUIDE.md` for detailed instructions on adjusting these values.

## Module Categories

### Essential for Pregnancy
- `pregnancy.json` - Core pregnancy module (modified for custom module integration)
- `female_reproduction.json` - Reproductive cycles (modified for increased frequency)
- `sexual_activity.json` - Sexual activity rates (modified for increased frequency)
- `contraceptives.json` - Contraceptive use (modified for reduced use)

### High Medication Generators
- `hypertension.json` + `medications/hypertension_medication.json` - ACE/ARB, beta blockers (contraindicated in pregnancy)
- `medications/ace_arb.json` - 68+ medications
- `medications/beta_blocker.json` - 46+ medications
- `medications/statin.json` - 34+ medications (contraindicated in pregnancy)
- `asthma.json` + `medications/maintenance_inhaler.json` + `medications/emergency_inhaler.json` - Common in pregnancy
- `metabolic_syndrome_disease.json` + `metabolic_syndrome/medications.json` - Diabetes medications (pregnancy risk)
- `urinary_tract_infections.json` + `uti/` submodules - Antibiotics (common in pregnancy)

### Mental Health
- `veteran_mdd.json` - SSRIs (pregnancy considerations)
- `veteran_ptsd.json` - Psych medications (pregnancy considerations)

### Chronic Pain/Opioids
- `prescribing_opioids_for_chronic_pain_and_treatment_of_oud.json` - 28+ medications
- `opioid_addiction.json` - Opioids (pregnancy risk)
- `medications/moderate_opioid_pain_reliever.json`
- `medications/strong_opioid_pain_reliever.json`

### Autoimmune
- `rheumatoid_arthritis.json` - DMARDs (pregnancy risk)
- `lupus.json` - Immunosuppressants (pregnancy risk)
- `fibromyalgia.json` - Chronic pain medications

### Other Conditions
- `epilepsy.json` - Anticonvulsants (teratogenic risk)
- `hypothyroidism.json` - Thyroid medications (important in pregnancy)
- `breast_cancer.json` + submodules - Chemotherapy, hormone therapy
- `allergies.json` + submodules - Drug allergies (critical for medication safety)

## Custom Modules Integration

This module set is designed to work with custom modules in `../my_modules/`:

- `gestational_weeks.json` - Called automatically during pregnancy
- `pregnancy_exposures.json` - Called automatically during pregnancy
- `lactation_status.json` - Called automatically after birth

These custom modules are loaded via:
- `modules.directory = ./modules_to_use` in `my.properties` (if they're in this directory), OR
- `MODULES_DIR=../my_modules` to add them on top

## Usage

These modules are used as the **ONLY** modules (excluding Synthea defaults) when:

```bash
# In my.properties:
modules.directory = ./modules_to_use
modules.exclude = *
```

Or as **ADDITIONAL** modules on top of defaults when:

```bash
# Set in environment:
MODULES_DIR=./modules_to_use ./run_synthea.sh
```

## Expected Results

With these modules:
- **High medication generation:** 5-15+ medications per patient
- **Pregnancy-relevant medications:** Most conditions have pregnancy interactions
- **Increased pregnancy frequency:** Modified modules generate more pregnancies
- **Comprehensive tracking:** Gestational age, pregnancy exposures, and lactation status

## Notes

- All modules maintain their original functionality
- Only pregnancy-related modules and frequency-controlling modules have been modified
- Medication generation remains unchanged from original Synthea modules
- Custom module integration is transparent to the rest of the module set
