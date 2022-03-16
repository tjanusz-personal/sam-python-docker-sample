import pytest
from ecshelpers.docker_image_analyzer import dockerImageAnalyzer
import botocore
import boto3
from botocore.stub import Stubber


# define some fixtures to make code cleaner
@pytest.fixture
def analyzer_instance():
    return dockerImageAnalyzer(False)

@pytest.fixture
def ecr_repo_base_ref():
    return "99999999.dkr.ecr.us-east-1.amazonaws.com/"

def test_extract_image_info_dev_ui_image_feature_branch(assertions, analyzer_instance, ecr_repo_base_ref):
    dev_image_info = ecr_repo_base_ref + "pets/dev/pets-ui:feature__feat1-build30-dev01_base-14.17.6_2022.01.13-slim"
    ecr_repo = ecr_repo_base_ref + "pets/dev/pets-ui"
    image_tag = "feature__feat1-build30-dev01_base-14.17.6_2022.01.13-slim"
    image_base = "14.17.6_2022.01.13-slim"
    result = analyzer_instance.extract_image_info(dev_image_info)
    expected_result = { 'tag' : image_tag, 'base' : image_base, 'repo' : ecr_repo }
    assertions.assertEqual(result, expected_result) 

def test_extract_image_info_dev_ui_image_dev_branch(assertions, analyzer_instance, ecr_repo_base_ref):
    dev_image_info = ecr_repo_base_ref + "pets/dev/pets-ui:develop-build30-dev01_base-14.17.6_2022.01.13-slim"
    ecr_repo = ecr_repo_base_ref + "pets/dev/pets-ui"
    image_tag = "develop-build30-dev01_base-14.17.6_2022.01.13-slim"
    image_base = "14.17.6_2022.01.13-slim"
    result = analyzer_instance.extract_image_info(dev_image_info)
    expected_result = { 'tag' : image_tag, 'base' : image_base, 'repo' : ecr_repo }
    assertions.assertEqual(result, expected_result) 

def test_extract_image_info_dev_svc_image_dev_branch(assertions, analyzer_instance, ecr_repo_base_ref):
    dev_svc_image = ecr_repo_base_ref + "pets/dev/pets-svc:develop-build30-dev01_base-2021.09.25"
    ecr_repo = ecr_repo_base_ref + "pets/dev/pets-svc"
    image_tag = "develop-build30-dev01_base-2021.09.25"
    image_base = "2021.09.25"
    result = analyzer_instance.extract_image_info(dev_svc_image)
    expected_result = { 'tag' : image_tag, 'base' : image_base, 'repo' : ecr_repo }
    assertions.assertEqual(result, expected_result) 

def test_extract_image_info_rel_ui_image(assertions, analyzer_instance, ecr_repo_base_ref):
    rel_ui_image = ecr_repo_base_ref + "pets/rel/pets-ui:1.1.1_base-14.17.6_2022.01.13-slim"
    ecr_repo = ecr_repo_base_ref + "pets/rel/pets-ui"
    image_tag = "1.1.1_base-14.17.6_2022.01.13-slim"
    image_base = "14.17.6_2022.01.13-slim"
    result = analyzer_instance.extract_image_info(rel_ui_image)
    expected_result = { 'tag' : image_tag, 'base' : image_base, 'repo' : ecr_repo }
    assertions.assertEqual(result, expected_result) 

def test_extract_image_info_rel_svc_image(assertions, analyzer_instance, ecr_repo_base_ref):
    rel_image_info = ecr_repo_base_ref + "pets/rel/pets-svc:1.1.1_base-2021.09.25"
    ecr_repo = ecr_repo_base_ref + "pets/rel/pets-svc"
    image_tag = "1.1.1_base-2021.09.25"
    image_base = "2021.09.25"
    result = analyzer_instance.extract_image_info(rel_image_info)
    expected_result = { 'tag' : image_tag, 'base' : image_base, 'repo' : ecr_repo }
    assertions.assertEqual(result, expected_result)

def test_extract_image_info_returns_empty_info_when_no_repo_found(assertions, analyzer_instance):
    dev_image_info = "feature__feat1-build30-dev01_base-14.17.6_2022.01.13-slim"
    result = analyzer_instance.extract_image_info(dev_image_info)
    expected_result = { 'tag' : '', 'base' : '', 'repo' : '' }
    assertions.assertEqual(result, expected_result) 

def test_extract_image_info_returns_partial_info_when_no_base_image_found(assertions, analyzer_instance, ecr_repo_base_ref):
    rel_image_info = ecr_repo_base_ref + "pets/rel/pets-svc:1.1.1-2021.09.25"
    ecr_repo = ecr_repo_base_ref + "pets/rel/pets-svc"
    image_tag = "1.1.1-2021.09.25"
    result = analyzer_instance.extract_image_info(rel_image_info)
    expected_result = { 'tag' : image_tag, 'base' : '', 'repo' : ecr_repo }
    assertions.assertEqual(result, expected_result) 

@pytest.mark.parametrize("image_str", [ "pets/rel/pets-svc:1.1.1_base-2021.09.25", "pets/rel/pets-ui:1.1.1_base-14.17.6_2022.01.13-slim"])
def test_image_matches_bases_returns_true_for_matching_image(image_str, assertions, analyzer_instance, ecr_repo_base_ref):
    valid_base_images = [ "14.17.6_2022.01.13-slim", "2021.09.25" ]
    rel_image_info = ecr_repo_base_ref + image_str
    result = analyzer_instance.image_matches_current_bases(rel_image_info, valid_base_images)
    assertions.assertEqual(True, result)

@pytest.mark.parametrize("image_str", [ "pets/rel/pets-svc:1.1.1_base-2021.08.22", "pets/rel/pets-ui:1.1.1_base-14.17.6_2022.01.11-slim"])
def test_image_matches_bases_returs_false_for_non_matching_image(image_str, assertions, analyzer_instance, ecr_repo_base_ref):
    valid_base_images = [ "14.17.6_2022.01.13-slim", "2021.09.25" ]
    rel_image_info = ecr_repo_base_ref + image_str
    result = analyzer_instance.image_matches_current_bases(rel_image_info, valid_base_images)
    assertions.assertEqual(False, result)

@pytest.mark.aws_integration
def test_fetch_base_images_from_s3_integration(analyzer_instance, assertions):
    s3_bucket_name = "tjanusz-personal-demo-stuff"
    s3_object_key = "dockerImagesSecInfo/validBaseImages.csv"
    base_images = analyzer_instance.fetch_base_images_from_s3(s3_bucket_name, s3_object_key)
    assertions.assertEqual(3, len(base_images))

@pytest.mark.aws_integration
def test_fetch_base_images_from_s3_throws_error_with_bad_key(analyzer_instance, assertions):
    s3_bucket_name = "tjanusz-personal-demo-stuff"
    s3_object_key = "dockerImagesSecInfo/bad_key_name"
    with pytest.raises(botocore.exceptions.ClientError) as exec_info:
        analyzer_instance.fetch_base_images_from_s3(s3_bucket_name, s3_object_key)

    assertions.assertEqual(exec_info.typename, "NoSuchKey")

@pytest.mark.aws_integration
def test_fetch_base_images_from_s3_throws_error_with_bad_bucket_name(analyzer_instance, assertions):
    s3_bucket_name = "tjanusz-personal-demo-stuff2"
    s3_object_key = "dockerImagesSecInfo/bad_key_name"
    with pytest.raises(botocore.exceptions.ClientError) as exec_info:
        analyzer_instance.fetch_base_images_from_s3(s3_bucket_name, s3_object_key)
    assertions.assertEqual(exec_info.typename, "NoSuchBucket")

def test_fetch_base_images_from_s3_throws_error_with_bad_key_using_mock(analyzer_instance, assertions):
    # create client and stubber around it
    s3_client = boto3.client('s3')
    stubber = Stubber(s3_client)
    stubber.add_client_error("get_object", service_error_code="NoSuchKey", service_message="Something went wrong")
    stubber.activate()
    with pytest.raises(botocore.exceptions.ClientError) as exec_info:
        analyzer_instance.fetch_base_images_from_s3("tjanusz-personal-demo-stuff", "object_key", s3_client)
    stubber.deactivate()
    assertions.assertEqual(exec_info.typename, "NoSuchKey")

def test_fetch_base_images_from_s3_throws_error_with_bad_bucket_using_mock(analyzer_instance, assertions):
    # create client and stubber around it
    s3_client = boto3.client('s3')
    stubber = Stubber(s3_client)
    stubber.add_client_error("get_object", service_error_code="NoSuchBucket", service_message="Something went wrong")
    stubber.activate()
    with pytest.raises(botocore.exceptions.ClientError) as exec_info:
        analyzer_instance.fetch_base_images_from_s3("tjanusz-personal-demo-stuff", "object_key", s3_client)
    stubber.deactivate()
    assertions.assertEqual(exec_info.typename, "NoSuchBucket")

