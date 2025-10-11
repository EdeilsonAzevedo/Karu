from django.db import connection

with connection.cursor() as cursor:
    patient_id = '4f4f220d-1407-48c5-b2e7-44d9c724ccc1' #Id do paciente
    
    print("🗑️  Excluindo na ORDEM CORRETA...")
    
    # PRIMEIRO: Excluir apenas os EmailAlerts que referenciam o paciente
    cursor.execute("DELETE FROM emails_emailalert WHERE patient_id = %s", [patient_id])
    
    # SEGUNDO: Excluir Records (o CASCADE deve cuidar do resto)
    cursor.execute("DELETE FROM patients_record WHERE patient_id = %s", [patient_id])
    
    # TERCEIRO: Excluir Patient
    cursor.execute("DELETE FROM patients_patient WHERE id = %s", [patient_id])
    
    print("✅✅✅ PACIENTE EXCLUÍDO!")