from typing import List
import boto3

class ecsUtils:
    ''' Simple methods for interacting with ECS tasks w/in an account.'''

    def __init__(self, verbose_mode = False, aws_profile: str = 'default', session: boto3.Session = None) -> None:
        if not session:
            session = boto3.Session(profile_name=aws_profile)

        self.ecs_client = session.client('ecs')
        self.verbose_mode = verbose_mode

    def get_cluster_info(self, cluster_name) -> list:
        """
            Print out cluster info (base boto wrapped call)
        """ 
        response = self.ecs_client.describe_clusters( clusters = [cluster_name])
        if self.verbose_mode:
            print("## Cluster Info:")
        
        results = []
        for a_cluster in response.get('clusters', []):
            cluster_info = 'Name: {0} Arn: {1}'.format(a_cluster.get('clusterName', 'N/A'), a_cluster.get('clusterArn', 'N/A'))
            results.append(cluster_info)
            if self.verbose_mode:
                print(cluster_info)

        return results

    def get_task_arns(self, cluster_name, task_status) -> list:
        """
            Retrieve all task arns for a given cluster (across all services)
            Parameters:
            cluster_name: the name of the cluster to use
            task_status: STOPPED, etc..  Must be valid boto3 status

            Returns:
            list of task_arns
        """ 

        if self.verbose_mode:
            print("### Pulling tasks")

        # list out tasks to find for this cluster (STOPPED)
        ecs_tasks = self.ecs_client.list_tasks(cluster = cluster_name, desiredStatus = task_status)
        if self.verbose_mode:
            print(ecs_tasks)

        # collect up task arns
        task_arns = [i for i in ecs_tasks.get('taskArns', [])]
        if self.verbose_mode:
            for a_task_arn in task_arns:
                print(a_task_arn)

        return task_arns

    def get_image_info_for_tasks(self, cluster_name, task_status) -> list:
        """
            Retrieve docker image info for all task arns for a given cluster (across all services)
            Parameters:
            cluster_name: the name of the cluster to use
            task_status: STOPPED, etc..  Must be valid boto3 status

            Returns:
            list of docker image info (Name, digest, image) for the images running w/in the containers on the tasks
        """

        task_arns = self.get_task_arns(cluster_name, task_status)

        if not task_arns:
            print("No task ARNs found")
            return []

        # pull out the details of the tasks related to docker images
        if self.verbose_mode:
            print("### Pulling tasks details to find docker images")

        task_descriptions = self.ecs_client.describe_tasks(cluster = cluster_name, tasks = task_arns)
        image_infos = []

        for a_task_def in task_descriptions.get('tasks', []):
            group_info = a_task_def.get('group', 'unknown')
            cluster_arn = a_task_def.get('clusterArn', 'unknown')
            account_id = self.extract_account_id_from_cluster_arn(cluster_arn)
            all_containers = a_task_def.get('containers', [])
            for a_container in all_containers:
                image_info = { 
                    'name' : a_container.get('name','N/A'), 
                    'image': a_container.get('image','N/A'), 
                    'imageDigest': a_container.get('imageDigest','N/A'),
                    'group' : group_info,
                    'cluster_arn': cluster_arn,
                    'account_id': account_id
                    }
                image_infos.append(image_info)

        return image_infos

    def extract_account_id_from_cluster_arn(self, cluster_arn) -> str:
        # "arn:aws:ecs:us-east-1:123456789012:cluster/TestCluster1"
        tokens = cluster_arn.split(":")
        if len(tokens) > 5:
            return tokens[4]
        return "unknown"