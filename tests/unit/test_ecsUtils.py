import pytest
from botocore.stub import Stubber
from ecshelpers.ecs_utils import ecsUtils
import boto3

# define some fixtures to make code cleaner
@pytest.fixture
def utils_instance():
    return ecsUtils(False)

def test_get_cluster_info_validates_args(assertions, utils_instance):
    stubber = Stubber(utils_instance.ecs_client)

    stub_response = {
        'clusters': [
            {
                'clusterName': 'clusterName1',
                'clusterArn' : 'arn:aws:ecs:us-west-2:123456789012:cluster/default',
                'status' : 'ACTIVE'
            }
        ]
    }
    expected_params = {'clusters': [ 'clusterName1']}

    stubber.add_response('describe_clusters', stub_response, expected_params)
    stubber.activate()
    results = utils_instance.get_cluster_info('clusterName1')
    stubber.deactivate()
    assert len(results) == 1

def test_get_task_arns_returns_tasks_from_cluster(assertions, utils_instance):
    stubber = Stubber(utils_instance.ecs_client)
    stub_response = { 
        'taskArns': [ 
            "arn:aws:ecs:us-west-2:123456789012:task/a1b2c3d4-5678-90ab-cdef-11111EXAMPLE",
            "arn:aws:ecs:us-west-2:123456789012:task/a1b2c3d4-5678-90ab-cdef-22222EXAMPLE"]
        }
    expected_params = {
        'cluster': 'clusterName1',
        'desiredStatus': 'STOPPED'
    }
    stubber.add_response('list_tasks', stub_response, expected_params)
    stubber.activate()
    results = utils_instance.get_task_arns('clusterName1', "STOPPED")
    stubber.deactivate()
    assert len(results) == 2
    
def test_get_task_arns_returns_empty_array_when_no_tasks_found(assertions, utils_instance):
    stubber = Stubber(utils_instance.ecs_client)
    stub_response = { 
        'taskArns': [ ]
        }
    expected_params = {
        'cluster': 'clusterName1',
        'desiredStatus': 'STOPPED'
    }
    stubber.add_response('list_tasks', stub_response, expected_params)
    stubber.activate()
    results = utils_instance.get_task_arns('clusterName1', "STOPPED")
    stubber.deactivate()
    assert len(results) == 0

def test_get_image_info_for_tasks_invokes_apis_correctly(assertions, utils_instance):
    stubber = Stubber(utils_instance.ecs_client)
    stubbedTaskArns = [ 
        "arn:aws:ecs:us-west-2:123456789012:task/a1b2c3d4-5678-90ab-cdef-11111EXAMPLE",
        "arn:aws:ecs:us-west-2:123456789012:task/a1b2c3d4-5678-90ab-cdef-22222EXAMPLE"
    ]

    # stub out list_tasks call
    list_tasks_stub_response = { 
        'taskArns': stubbedTaskArns
        }
    list_tasks_expected_params = {
        'cluster': 'TestCluster1',
        'desiredStatus': 'STOPPED'
    }
    stubber.add_response('list_tasks', list_tasks_stub_response, list_tasks_expected_params)

    desc_tasks_stub_response = { 
        'tasks': [
            {
                'taskArn': 'arn:aws:ecs:us-west-2:123456789012:task/a1b2c3d4-5678-90ab-cdef-11111EXAMPLE',
                'group' : 'service:GtwServiceDef',
                'clusterArn': 'arn:aws:ecs:us-east-1:123456789012:cluster/TestCluster1',
                'containers': [
                    {
                        'name': 'container1',
                        'image': 'dockerImage1',
                        'imageDigest': 'sha256:d5e4'
                    }
                ]
            }
         ]
        }
    desc_tasks_expected_params = {
        'cluster': 'TestCluster1',
        'tasks': stubbedTaskArns
    }
    stubber.add_response('describe_tasks', desc_tasks_stub_response, desc_tasks_expected_params)
    stubber.activate()
    results = utils_instance.get_image_info_for_tasks('TestCluster1', 'STOPPED')
    assert len(results) == 1
    expected_info = {
        "name": "container1",
        "image": "dockerImage1",
        "imageDigest": "sha256:d5e4",
        "group": "service:GtwServiceDef",
        "cluster_arn": "arn:aws:ecs:us-east-1:123456789012:cluster/TestCluster1",
        "account_id": "123456789012"
    }
    assertions.assertEqual(expected_info, results[0])


@pytest.mark.aws_integration
def test_task_arns_invokes_aws_correctly(assertions, utils_instance):
    results = utils_instance.get_task_arns("TestCluster1", "STOPPED")
    assertions.assertTrue(len(results) >= 0)
    # super bad test since this all depends on what's running on the cluster at the time!
    # assertions.assertEqual(3, len(results))

@pytest.mark.aws_integration
def test_get_image_info_for_tasks(assertions, utils_instance):
    results = utils_instance.get_image_info_for_tasks('TestCluster1', 'STOPPED')
    assertions.assertTrue(len(results) >= 0)
    # super bad test since this all depends on what's running on the cluster at the time! I only use this to regression test
    # assertions.assertEqual('GtwSvcContainer', results[0]['Name'])
    # assertions.assertIn('demo-tomcat', results[0]['image'])
    # assertions.assertIn('sha256:', results[0]['imageDigest'])
    # print(results[0])

@pytest.mark.aws_integration
def test_get_cluster_info_with_config_invokes_aws_correctly(assertions):
    # session = boto3.Session(profile_name='default')
    utils_instance2 = ecsUtils(False, 'dev01')
    results = utils_instance2.get_cluster_info("TestCluster1")
    assertions.assertEqual(1, len(results))
    assertions.assertIn('TestCluster1', results[0])

def test_extract_account_id_from_cluster_arn(assertions, utils_instance):
    account_id = utils_instance.extract_account_id_from_cluster_arn("arn:aws:ecs:us-east-1:123456789012:cluster/TestCluster1")
    assertions.assertEqual("123456789012", account_id)

@pytest.mark.parametrize("cluster_arn", [ "arn:aws:ecs:us-east-1", "", "arn:aws:", "someStringWithNoColons"])
def test_extract_account_id_from_cluster_arn_returns_unknown(cluster_arn, assertions, utils_instance):
    account_id = utils_instance.extract_account_id_from_cluster_arn(cluster_arn)
    assertions.assertEqual("unknown", account_id)
