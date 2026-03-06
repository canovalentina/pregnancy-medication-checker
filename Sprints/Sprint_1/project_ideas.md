This document is for brainstorming potential ideas for the final project. 
# Lana
## Women's Health
### Pregnancy
- Focus on specific pregnancy issues: 
	- preeclampsia
	- postpartum depression
	- gestational diabetes
	- ectopic pregnancy
**ML Website Idea:**  
- Rules-based alerting for pregnancy complications  

**App Flow:**  
- Patient logs blood pressure / other symptoms  
- Data sent via **FHIR**  
- Clinician dashboard highlights high-risk patients (e.g., preeclampsia risk)  

**Sources:**  
- [NICHD Pregnancy Complications](https://www.nichd.nih.gov/health/topics/pregnancy/conditioninfo/complications)  
- [Hopkins Medicine – Complications of Pregnancy](https://www.hopkinsmedicine.org/health/conditions-and-diseases/staying-healthy-during-pregnancy/complications-of-pregnancy)  

---
### Endometriosis / PCOS
**Website Idea:**  
- Logs birth control side effects and visualizes data over a 3–6 month period  
- Helps determine whether dosage/brand switch is needed  
- Addresses real-world gap: side effect tracking is often not documented  

**Patient-Facing View:**  
- Track emotional variability, weight gain, fatigue, other side effects  
- Symptom diary (mood tracker, weight entry, side effects list)  
- Simple visualizations (graphs, weekly summaries)  

**Clinician-Facing View:**  
- Dashboard showing trends across 3–6 months  
- Patient list with risk indicators (e.g., “severe mood changes for >4 weeks”)  
- Trend dashboard for each patient  

**Standards Connection:**  
- Side effect data shared via **FHIR** to EMR  
- Rules-based alerting (e.g., “weight gain >10 lbs in 3 months”)  
- Exportable report for patient visits  

---

## Other General Project Areas of Interest
- Machine learning  
- Genomic sequencing  
- Data analytics  
- Public health  
- Clinical informatics  



# Faezeh
## Women's Health
### Postpartum Depression
- Issue: High rate of undiagnosed postpartum anxiety and depression.
- Probable reason(s): incosnsistent or incomplete follow up with the patient. Patient self censoring due to social concerns.
- Solution: recurrent screening and ongoing monitoring.
- Clinician side: establishing a standardized screening tool across providers, including the OBGYN, Pediatric, Psychiatry.
- Patient side: Providing a self assessment questionaire in form of a mobile application or patient poratl.  

### Women's Annual Checkup
- Issue: Missing screening lead to late disease diagnosis, resulting in more difficult and costly treatment.
- Checkups including: Pap smear, Mammogram, HPV, etc. 
- Probable reason(s): Busy schedules and procastination.
- Solution: Receiving reminders. Timely reminders and provider encouragement to maintain regular checkups.
- Clinician side: Automated reminders.Include a section in dashboard for tracking recommended checkups.
- Patient side: Receive reminders through email, SMS, patient portal, or voice mail. Providing educational content on the importance of regular screening. View screening results and reports in patient portal.

### Bone Health in women
- Issue: Many women experience some level of osteoporosis in midlife. Its important that women monitor bone density through preventive screening, before fracture occurs.
- Solution: Educating patients on healthy lifestyle and prevention.
- Clinician side: Provider can assess the patient's risk by evaluating factors such as age, family history and BMI from the patient's EHR, so that  recommended education and monitoring, can be delivered appropriately.
- Patient side: Receiving reminders for prevention screening. Receiving daily lifestyle recommendations through the patient portal, such as guidance on diet, exercise, and supplements.

## Other General Project Areas of Interest
- End user application (Patient data visualizer)
- Public health
- Social determinants of health

# Valentina
## Women's Health

### Medication Interactions and Side Effects in Women’s Health

- Issue: Psychiatric medications often interact with contraceptives, pregnancy-related meds, or lactation safety, and risks are rarely flagged. On the other hand, some medications are safe to take (or at least the pros outweigh the cons), but there a lot of doctors that have out-dated research.
- Idea: Medication Interaction Checker web app.
    * Patient enters medications into a mobile/web portal, as well as important context (menstrual cycle, pregnancy, lactation, diagnoses, etc.).
    * Backend checks for flagged interactions (e.g., SSRI + oral contraceptive = decreased efficacy).
    * The app also searches the web for the most recent research on the interactions.
    * Clinician dashboard displays flagged risks with color-coded severity levels + excerpts of important recent research.

### Preventive Care & Mental Health Dashboard (related to Women's Annual Checkup)

- Issue: Preventive screenings (Pap smear, mammogram, bone density) are rarely discussed in mental health follow-up, even though depression/anxiety predicts lower preventive care adherence.
- Idea: Clinician dashboard that integrates preventive care and mental health screening.
    * Dashboard combines physical health and mental health screening status.
    * Example: Patient overdue for mammogram AND hasn’t completed depression screening in 6 months.
    * Patient portal sends personalized reminders (SMS/email), and clinicians can have targeted follow-ups.
- Also investigate the general population trends. For example, “Patients with moderate depression are 40% less likely to complete mammograms”, to keep the clinicians and patients informed and motivated. We could use ML to predict the risk/likelihood of not completing the screenings, and use the risk to guide the clinician's decision-making.

### Mood Tracking Linked to Reproductive Health

- Issue: Mood disorders often fluctuate across menstrual cycle, pregnancy, and postpartum, but patients and providers lack integrated tracking tools.
- Idea: Patient-facing app with mood diary + symptom tracking, with visualizations and summarizations of the data for clinicians.
    * Patient self-reports daily mood, sleep, and medication adherence.
    * Can use weekly validated scales like GAD-7 for anxiety and EPDS for postpartum.
    * Rules-based alert system for clinicians.

