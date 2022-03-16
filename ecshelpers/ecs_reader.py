import json
import os
import csv
import boto3 

from ecs_utils import ecsUtils as ecsUtils
from docker_image_analyzer import dockerImageAnalyzer as dia


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format
        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict
        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    sts = boto3.client('sts')
    print(sts.get_caller_identity())

    # pull in buckeet and key for base images
    bucket_name = os.getenv('BUCKET_NAME')
    base_image_key = os.getenv('VALID_BASE_IMAGES_KEY')
    result_output_key = os.getenv('RESULT_OUTPUT_KEY')

    # fetch base images from S3
    dia_instance = dia(False)
    base_images = dia_instance.fetch_base_images_from_s3(bucket_name, base_image_key)
    # print(base_images)

    print("creating boto session")
    boto_session = boto3.Session()
    utils_instance = ecsUtils(verbose_mode = False, session=boto_session)

    print("pulling all ECS related tasks")
    # get all running image on the cluster
    task_results = utils_instance.get_image_info_for_tasks('TestCluster1', 'STOPPED')

    # decorate task result w/results of matchings to base images
    for task_result in task_results:
        result = dia_instance.image_matches_current_bases(task_result['image'], base_images)
        task_result['validBaseImage'] = result

    if len(task_results) > 0:
        write_results_to_s3(task_results, bucket_name, result_output_key)

    message = "app with env: {0} and baseImageKey: {1}".format(bucket_name, base_image_key)
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": message,
            }
        ),
    }

def write_results_to_s3(task_results, bucket_name, bucket_key):
    print(task_results)

    field_names = ['account_id', 'name', 'group', 'validBaseImage', 'image', 'imageDigest', 'cluster_arn']
    with open('/tmp/test1.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = field_names)
        writer.writeheader()
        writer.writerows(task_results)

    s3 = boto3.resource('s3')
    bucket_to_upload = s3.Bucket(bucket_name)

    bucket_to_upload.upload_file('/tmp/test1.csv', bucket_key)

def do_echo(a_string):
    return a_string 