import os
import json
import traceback
from fastapi import FastAPI, Request, HTTPException
from google.cloud import storage
from parser import extract_invoice_data

app = FastAPI(title="Parser Service (Direct HTTP)")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "operaciones-peru")
storage_client = storage.Client()

def read_xml_from_gcs(gcs_path):
    """Lee un archivo XML desde GCS y devuelve su contenido en bytes."""
    parts = gcs_path.replace("gs://", "").split("/", 1)
    bucket_name, file_path = parts
    blob = storage_client.bucket(bucket_name).blob(file_path)
    return blob.download_as_bytes()

@app.post("/parse-direct")
async def parse_direct(request: Request):
    """Endpoint directo para procesamiento síncrono desde el orquestador."""
    try:
        operation_data = await request.json()
        tracking_id = operation_data["tracking_id"]
        xml_paths = operation_data.get("gcs_paths", {}).get("xml", [])
        
        print(f"PARSER DIRECTO: Procesando {tracking_id} con {len(xml_paths)} XMLs.")
        
        parsed_invoices = []
        for xml_path in xml_paths:
            try:
                xml_content = read_xml_from_gcs(xml_path)
                invoice_data = extract_invoice_data(xml_content)
                invoice_data['xml_filename'] = xml_path.split('/')[-1]
                parsed_invoices.append(invoice_data)
            except Exception as e:
                print(f"PARSER DIRECTO: Error procesando {xml_path}: {e}")
                continue
        
        result = {"parsed_results": parsed_invoices}
        print(f"PARSER DIRECTO: {tracking_id} procesado exitosamente con {len(parsed_invoices)} facturas.")
        
        return result
        
    except Exception as e:
        print(f"PARSER DIRECTO: Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))