import json
import os

def lambda_handler(event, context):
    bucket_name = os.getenv('BUCKET_NAME')
    base_image_key = os.getenv('VALID_BASE_IMAGES_KEY')
    message = "hello world from app2 with env: {0} and baseImageKey: {1}".format(bucket_name, base_image_key)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": message,
            }
        ),
    }
