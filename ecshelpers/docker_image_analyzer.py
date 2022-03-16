from typing import List
import boto3
import csv

class dockerImageAnalyzer:
    ''' Simple methods for decomposing relevant info for the ECS docker images we need (e.g. image name, base image used, etc.'''

    def __init__(self, verbose_mode = False) -> None:
        self.verbose_mode = verbose_mode

    def extract_image_info(self, full_image_string) -> dict[str, str]:
        """
            Extract out the different parts of the image we need (e.g. tag, base, repo)
            Our tagging strategy includes base image info w/in it so using the full tag name permits us to know the base image w/out having to inspect dockerfile.
            Right now we only need to know which docker images have CVEs on them but we will need to also compare to what our valid base image names are too to 
            find out which running images need to be rebuilt/patched.
        """

        # devImageInfo = "99999999.dkr.ecr.us-east-1.amazonaws.com/pets/dev/pets-ui:feature__feat1-build30-dev01_base-14.17.6_2022.01.13-slim"
        # ecr_repo = "99999999.dkr.ecr.us-east-1.amazonaws.com/pets/dev/pets-ui"
        # imageTag = "feature__feat1-build30-dev01_base-14.17.6_2022.01.13-slim"
        # imageBase = "14.17.6_2022.01.13-slim"
        image_info = {
            'tag' : '',
            'base' : '',
            'repo' : ''
        }   

        # split out repo name first
        repo_splits = full_image_string.split(":", 1)
        if len(repo_splits) < 2:
            return image_info

        image_info['repo'] = repo_splits[0]
        image_info['tag'] = repo_splits[1]

        # split out tag info
        tag_splits = repo_splits[1].split("_base-", 1)
        if len(tag_splits) < 2:
            return image_info

        image_info['base'] = tag_splits[1]
        return image_info

    def image_matches_current_bases(self, full_image_string, valid_base_images) -> bool:
        # given a full string return if matches valid base image
        image_info = self.extract_image_info(full_image_string)
        return image_info['base'] in valid_base_images

    def fetch_base_images_from_s3(self, bucket_name, s3Key, s3_client = None) -> list[str]:
        """
            retrieve the .csv file of our current valid base images from S3 and return as an array of strings
        """

        # pull a csv file from s3 and open and return list
        if not s3_client:
            s3_client = boto3.client('s3')

        data = s3_client.get_object(Bucket=bucket_name, Key=s3Key)
        
        # read the contents of the file and split it into a list of lines
        lines = data['Body'].read().decode('utf-8').split()      
        # print(len(lines))
        images = []
        for row in csv.DictReader(lines):
            images.append(row['image_tag'])

        return images
