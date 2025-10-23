import json
import os
import boto3 
import uuid   
from datetime import datetime

# YAML'da tanımlanan tablo adını al
TABLE_NAME = os.environ.get('TABLE_NAME', 'default-table')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Bu fonksiyon iki API endpoint'ini yönetir:
    POST /visit -> Yeni ziyaretçi ekler
    GET /visits -> Son 10 ziyaretçiyi listeler
    """
    
    try:
        http_method = event['requestContext']['http']['method']
        path = event['requestContext']['http']['path']
    except KeyError:
        return _response(400, {"error": "Invalid request format (not HTTP API?)"})

    # -------------------------------
    # YÖNLENDİRİCİ (ROUTER)
    # -------------------------------
    
    # SENARYO 1: POST /visit (prod stage'i path'e dahil olabilir)
    if http_method == "POST" and path.endswith("/visit"):
        try:
            body = json.loads(event.get('body', '{}'))
            name = body.get('name')
            
            if not name:
                return _response(400, {"error": "Missing 'name' in request body"})
            
            item = {
                'id': str(uuid.uuid4()), 
                'name': name,
                'visit_time': datetime.utcnow().isoformat()
            }
            
            table.put_item(Item=item)
            
            return _response(201, {"message": "Visit recorded successfully", "item": item})
        
        except json.JSONDecodeError:
            return _response(400, {"error": "Invalid JSON in request body"})
        except Exception as e:
            return _response(500, {"error": "Internal server error", "details": str(e)})

    # SENARYO 2: GET /visits
    elif http_method == "GET" and path.endswith("/visits"):
        try:
            # Not: Scan, büyük tablolarda yavaştır. Demo amaçlıdır.
            response = table.scan(Limit=20) 
            items = response.get('Items', [])
            
            # Ziyaret zamanına göre tersten sırala (en yeni en üstte)
            items_sorted = sorted(items, key=lambda x: x['visit_time'], reverse=True)
            
            return _response(200, {"visits": items_sorted})
        except Exception as e:
            return _response(500, {"error": "Internal server error", "details": str(e)})

    # SENARYO 3: Diğer tüm istekler
    return _response(404, {"error": "Not Found"})

def _response(status_code, body_object):
    """API Gateway HTTP API için standart yanıt formatı"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body_object, ensure_ascii=False)
    }