# Creating XML form templates and a field checklist CSV for CommCare (Visit, Inventory, Facility Log),
# plus a manifest CSV. Files will be saved to /mnt/data so you can download them.
from pathlib import Path

base = Path("data2/commcare_forms")
base.mkdir(parents=True, exist_ok=True)

visit_xml = """<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms"
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:jr="http://openrosa.org/javarosa">
  <h:head>
    <h:title>Visit / Consultation Form</h:title>
    <model>
      <instance>
        <data id="visit_consultation">
          <!-- Backend will attach: visit_uuid, created_at, updated_at, facility_id -->
          <visit_ref/>
          <patient_ref/>
          <visit_date/>
          <presenting_complaint/>
          <symptoms/>
          <temperature/>
          <blood_pressure_systolic/>
          <blood_pressure_diastolic/>
          <weight_kg/>
          <height_cm/>
          <provisional_diagnosis/>
          <laboratory_tests_ordered/>
          <lab_results/>
          <treatment_given/>
          <medicines_dispensed/>
          <referral_made/>
          <referral_facility/>
          <follow_up_date/>
          <outcome/>
          <attending_staff/>
          <staff_cadre/>
          <notes/>
        </data>
      </instance>

      <bind nodeset="/data/visit_ref" type="string" required="true()"/>
      <bind nodeset="/data/patient_ref" type="string" required="true()"/>
      <bind nodeset="/data/visit_date" type="date" required="true()"/>
      <bind nodeset="/data/temperature" type="decimal" constraint=". &gt;= 30 and . &lt;= 45"/>
      <bind nodeset="/data/blood_pressure_systolic" type="int" constraint=". &gt;= 50 and . &lt;= 250"/>
      <bind nodeset="/data/blood_pressure_diastolic" type="int" constraint=". &gt;= 30 and . &lt;= 150"/>
    </model>
  </h:head>

  <h:body>
    <input ref="/data/visit_ref"><label>Visit Reference (back-end populated)</label></input>
    <input ref="/data/patient_ref"><label>Patient Reference (select or lookup)</label></input>
    <input ref="/data/visit_date"><label>Date of Visit</label></input>
    <input ref="/data/presenting_complaint"><label>Presenting Complaint</label></input>
    <input ref="/data/symptoms"><label>Symptoms (comma-separated)</label></input>
    <group ref="/data/temperature">
      <label>Vitals</label>
      <input ref="/data/temperature"><label>Temperature (°C)</label></input>
      <input ref="/data/blood_pressure_systolic"><label>BP Systolic</label></input>
      <input ref="/data/blood_pressure_diastolic"><label>BP Diastolic</label></input>
      <input ref="/data/weight_kg"><label>Weight (kg)</label></input>
      <input ref="/data/height_cm"><label>Height (cm)</label></input>
    </group>
    <input ref="/data/provisional_diagnosis"><label>Provisional Diagnosis</label></input>
    <select1 ref="/data/laboratory_tests_ordered">
      <label>Lab Tests Ordered</label>
      <item><label>None</label><value>none</value></item>
      <item><label>Malaria RDT</label><value>malaria_rdt</value></item>
      <item><label>RBS</label><value>rbs</value></item>
      <item><label>Other</label><value>other</value></item>
    </select1>
    <input ref="/data/lab_results"><label>Lab Results</label></input>
    <input ref="/data/treatment_given"><label>Treatment Given</label></input>
    <input ref="/data/medicines_dispensed"><label>Medicines Dispensed (names & qty)</label></input>
    <select1 ref="/data/referral_made">
      <label>Referral Made?</label>
      <item><label>No</label><value>no</value></item>
      <item><label>Yes</label><value>yes</value></item>
    </select1>
    <input ref="/data/referral_facility"><label>If referred, Facility</label></input>
    <input ref="/data/follow_up_date"><label>Follow-up Date</label></input>
    <select1 ref="/data/outcome">
      <label>Outcome</label>
      <item><label>Recovered</label><value>recovered</value></item>
      <item><label>Referred</label><value>referred</value></item>
      <item><label>Died</label><value>died</value></item>
      <item><label>Ongoing</label><value>ongoing</value></item>
    </select1>
    <input ref="/data/attending_staff"><label>Attending Staff (name)</label></input>
    <select1 ref="/data/staff_cadre">
      <label>Staff Cadre</label>
      <item><label>CHEW</label><value>chew</value></item>
      <item><label>Nurse</label><value>nurse</value></item>
      <item><label>Doctor</label><value>doctor</value></item>
      <item><label>Midwife</label><value>midwife</value></item>
    </select1>
    <input ref="/data/notes"><label>Clinical Notes</label></input>
  </h:body>
</h:html>
"""

stock_xml = """<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms"
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:jr="http://openrosa.org/javarosa">
  <h:head>
    <h:title>Inventory / Stock Update</h:title>
    <model>
      <instance>
        <data id="inventory_stock_update">
          <!-- Backend will attach: inventory_uuid, created_at, facility_id -->
          <stock_update_ref/>
          <item_code/>
          <item_name/>
          <opening_balance/>
          <quantity_received/>
          <quantity_issued/>
          <adjustments/>
          <closing_balance/>
          <expiry_date/>
          <stock_out_flag/>
          <report_date/>
          <reported_by/>
          <notes/>
        </data>
      </instance>

      <bind nodeset="/data/stock_update_ref" type="string" required="true()"/>
      <bind nodeset="/data/item_code" type="string" required="true()"/>
      <bind nodeset="/data/opening_balance" type="int" constraint=". &gt;= 0"/>
      <bind nodeset="/data/quantity_received" type="int" constraint=". &gt;= 0"/>
      <bind nodeset="/data/quantity_issued" type="int" constraint=". &gt;= 0"/>
      <bind nodeset="/data/closing_balance" type="int" constraint=". &gt;= 0"/>
      <bind nodeset="/data/stock_out_flag" type="boolean"/>
      <bind nodeset="/data/report_date" type="date" required="true()"/>
    </model>
  </h:head>

  <h:body>
    <input ref="/data/stock_update_ref"><label>Stock Update Reference (backend populated)</label></input>
    <input ref="/data/item_code"><label>Item Code</label></input>
    <input ref="/data/item_name"><label>Item Name</label></input>
    <input ref="/data/opening_balance"><label>Opening Balance</label></input>
    <input ref="/data/quantity_received"><label>Quantity Received</label></input>
    <input ref="/data/quantity_issued"><label>Quantity Issued</label></input>
    <input ref="/data/adjustments"><label>Adjustments (if any)</label></input>
    <input ref="/data/closing_balance"><label>Closing Balance</label></input>
    <input ref="/data/expiry_date"><label>Expiry Date</label></input>
    <select1 ref="/data/stock_out_flag">
      <label>Stock-out?</label>
      <item><label>No</label><value>false</value></item>
      <item><label>Yes</label><value>true</value></item>
    </select1>
    <input ref="/data/report_date"><label>Report Date</label></input>
    <input ref="/data/reported_by"><label>Reported By (name)</label></input>
    <input ref="/data/notes"><label>Notes</label></input>
  </h:body>
</h:html>
"""

facility_xml = """<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms"
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:jr="http://openrosa.org/javarosa">
  <h:head>
    <h:title>Facility Performance Log</h:title>
    <model>
      <instance>
        <data id="facility_performance_log">
          <!-- Backend will attach: log_uuid, created_at, facility_id -->
          <facility_ref/>
          <reporting_date/>
          <num_staff_on_duty/>
          <num_patients_seen/>
          <num_deliveries/>
          <num_immunizations/>
          <num_referrals/>
          <electricity_functional/>
          <water_functional/>
          <open_status/>
          <notes/>
        </data>
      </instance>

      <bind nodeset="/data/facility_ref" type="string" required="true()"/>
      <bind nodeset="/data/reporting_date" type="date" required="true()"/>
      <bind nodeset="/data/num_staff_on_duty" type="int" constraint=". &gt;= 0"/>
      <bind nodeset="/data/num_patients_seen" type="int" constraint=". &gt;= 0"/>
    </model>
  </h:head>

  <h:body>
    <input ref="/data/facility_ref"><label>Facility Reference (select)</label></input>
    <input ref="/data/reporting_date"><label>Reporting Date</label></input>
    <input ref="/data/num_staff_on_duty"><label>Number of Staff on Duty</label></input>
    <input ref="/data/num_patients_seen"><label>Number of Patients Seen</label></input>
    <input ref="/data/num_deliveries"><label>Number of Deliveries</label></input>
    <input ref="/data/num_immunizations"><label>Number of Immunizations</label></input>
    <input ref="/data/num_referrals"><label>Number of Referrals</label></input>
    <select1 ref="/data/electricity_functional">
      <label>Electricity Functional?</label>
      <item><label>No</label><value>false</value></item>
      <item><label>Yes</label><value>true</value></item>
    </select1>
    <select1 ref="/data/water_functional">
      <label>Water Functional?</label><value>true</value></select1>
    <select1 ref="/data/open_status">
      <label>Open Status</label>
      <item><label>Open</label><value>open</value></item>
      <item><label>Closed</label><value>closed</value></item>
      <item><label>Partial</label><value>partial</value></item>
    </select1>
    <input ref="/data/notes"><label>Notes</label></input>
  </h:body>
</h:html>
"""

# Field checklist CSV
checklist = """form_name,field_name,data_type,required,description,notes
patient_registration,patient_id,string,yes,Unique patient reference (backend preferred),Provide name fields; backend assigns UUID
patient_registration,first_name,string,yes,First name,
patient_registration,last_name,string,no,Last name,
patient_registration,sex,select_one,yes,Sex (M/F),
patient_registration,date_of_birth,date,yes,Date of birth,
patient_registration,phone_number,string,no,Contact number,
patient_registration,state,select_one,yes,State where facility is located,
patient_registration,lga,select_one,yes,LGA,
patient_registration,facility_name,select_one,yes,Facility (case or lookup),
patient_registration,nhmis_service_type,select_one,yes,Service category (OPD/ANC/IMM),
patient_registration,hiv_status,select_one,no,HIV status,
patient_registration,pregnant,boolean,no,If pregnant (Y/N),
visit_consultation,visit_ref,string,yes,Visit reference (backend-generated),Accept backend UUID in payload
visit_consultation,patient_ref,string,yes,Reference to patient case (select/lookup),Can be patient UUID or commcare case id
visit_consultation,visit_date,date,yes,Date of encounter,
visit_consultation,presenting_complaint,string,no,Chief complaint,
visit_consultation,symptoms,string,no,Symptoms (comma-separated),
visit_consultation,temperature,decimal,no,Temperature in Celsius,
visit_consultation,blood_pressure_systolic,int,no,BP systolic,
visit_consultation,blood_pressure_diastolic,int,no,BP diastolic,
visit_consultation,weight_kg,decimal,no,Weight (kg),
visit_consultation,height_cm,decimal,no,Height (cm),
visit_consultation,provisional_diagnosis,select_one,yes,Provisional diagnosis (ICD or local),
visit_consultation,laboratory_tests_ordered,select_one,no,Which lab tests were ordered,
visit_consultation,lab_results,string,no,Lab results,
visit_consultation,treatment_given,string,no,Treatment given,
visit_consultation,medicines_dispensed,string,no,Medicines dispensed (name:qty),
visit_consultation,referral_made,select_one,no,Referral made (yes/no),
visit_consultation,referral_facility,string,no,If referred - facility,
visit_consultation,follow_up_date,date,no,Follow-up date,
visit_consultation,outcome,select_one,no,Outcome of visit,
visit_consultation,attending_staff,string,no,Name of attending staff,
visit_consultation,staff_cadre,select_one,no,Staff cadre (CHEW/Nurse/Doctor),
visit_consultation,notes,string,no,Clinical notes,
inventory_stock_update,stock_update_ref,string,yes,Stock update reference (backend-generated),
inventory_stock_update,item_code,string,yes,Item code (use standard catalogue if possible),
inventory_stock_update,item_name,string,yes,Item name,
inventory_stock_update,opening_balance,int,yes,Opening stock balance,
inventory_stock_update,quantity_received,int,no,Quantity received since last report,
inventory_stock_update,quantity_issued,int,no,Quantity issued/dispensed,
inventory_stock_update,adjustments,int,no,Manual adjustments,
inventory_stock_update,closing_balance,int,yes,Calculated closing balance (or reported),
inventory_stock_update,expiry_date,date,no,Expiry date of batch,
inventory_stock_update,stock_out_flag,boolean,no,Flag if stockout observed,
inventory_stock_update,report_date,date,yes,Date of report,
inventory_stock_update,reported_by,string,no,Name of reporter,
inventory_stock_update,notes,string,no,Notes,
facility_performance_log,facility_ref,string,yes,Facility reference (lookup/case id),
facility_performance_log,reporting_date,date,yes,Date of report (or month),
facility_performance_log,num_staff_on_duty,int,no,Number of staff on duty,
facility_performance_log,num_patients_seen,int,no,Number of patients seen,
facility_performance_log,num_deliveries,int,no,Number of deliveries,
facility_performance_log,num_immunizations,int,no,Number of immunizations given,
facility_performance_log,num_referrals,int,no,Number of referrals,
facility_performance_log,electricity_functional,boolean,no,Electricity available?,
facility_performance_log,water_functional,boolean,no,Water available?,
facility_performance_log,open_status,select_one,no,Facility open/closed/partial,
facility_performance_log,notes,string,no,Additional notes
"""

manifest = """dataset_name,filename,description,import_instructions
visit_consultation,visit_form.xml,CommCare XForm for Visit / Consultation,Upload via CommCare Form Upload (Applications > Advanced > Upload Form)
inventory_stock_update,stock_form.xml,CommCare XForm for Inventory / Stock Update,Upload via CommCare Form Upload
facility_performance_log,facility_log_form.xml,CommCare XForm for Facility Performance Log,Upload via CommCare Form Upload
field_checklist,field_checklist.csv,CSV checklist of fields and types,Use as reference when building or reviewing forms
"""

# Write files
visit_path = base / "visit_form.xml"
stock_path = base / "stock_form.xml"
facility_path = base / "facility_log_form.xml"
checklist_path = base / "field_checklist.csv"
manifest_path = base / "forms_manifest.csv"

visit_path.write_text(visit_xml, encoding="utf-8")
stock_path.write_text(stock_xml, encoding="utf-8")
facility_path.write_text(facility_xml, encoding="utf-8")
checklist_path.write_text(checklist, encoding="utf-8")
manifest_path.write_text(manifest, encoding="utf-8")

# List files for user
files = list(base.glob("*"))
files_list = "\n".join(str(p) for p in files)
files_list

