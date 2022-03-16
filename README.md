# sam-python-sample
This is sample SAM project for creating python based lambdas to be deployed as docker images. 

I created this to basically understand
* the limitations of using SAM and docker to deploy python based lambdas considering some of my current company's deployment restrictions.
* how we could interrogate our ECS clusters looking for the associated docker images to see if they're currently using our latest base images

The project contains two basic python lambdas.  Features include:
* Required configuration for creating python code as a docker image deployed to a private AWS ECR repository
* Demonstrates how to use SAM for two different lambdas being created/deployed w/in SAME docker image (NOT separate)
* Single parameterized template.yaml for deployment to different AWS account environments (dev, test) using samconfig.toml parameter definitions
* Attempt at understanding if/how docker tagging is impacted by utilizing SAM for build/deploy
* Lambda function policies specific to certain resources (e.g. S3 bucket)
* Lambda function reads ECS metadata looking for compliance to a base image standard (see ecs_reader Lambda section)

Creation Notes:
* 'sam init' with basic lambda template
* python3.9 runtime

## Lambda Function - ecs_reader
At my current employer we have a desire to determine which running ECS cluster's tasks docker images are 'up to date' with our current base image standards.  

This lambda attempts to determine this information by:
* Reading the tasks from all ECS clusters in the account
* Pulling out the related docker image information from the containers on the tasks
* Comparing those docker image tags to the current standard tagset
* Writing out any discrepancies to a S3 bucket location

|Parameter| Example Value | Description |
| --- | --- | --- |
|BUCKET_NAME | tjanusz-personal-demo-stuff | S3 bucket name where valid base image csv located|
|VALID_BASE_IMAGES_KEY| dockerImagesSecInfo/validBaseImages.csv| Object key for valid base image tags |
|RESULT_OUTPUT_KEY| dockerImagesSecInfo/scanResults1.csv | Object key to write output results to |

Valid base image csv file contents looks something like this
```csv
image_tag,image_type
"14.17.6_2022.01.13-slim","nodeJS"
"2021.09.25","tomcat"
"2021.10.22","python"
```

After running lambda outputted CSV file looks something like this
```csv
outputted CSV results
account_id,name,group,validBaseImage,image,imageDigest,cluster_arn
211287010274,SampleCoreSvcContainer,service:SampleCoreSvc,True,211287010274.dkr.ecr.us-east-1.amazonaws.com/sample-core-service:1.1.1_base-2021.09.25,N/A,arn:aws:ecs:us-east-1:211287010274:cluster/TestCluster1
```

Using this information we can easily install this onto our central account and schedule an event bridge event to kick this off on a given interval.


## Lambda Function - docker_image_analyzer
TODO: figure out what else I want to read from the docker image. right now this is just a shell. I have another project that examines the inspector2 results maybe i'll add that here.

## Python Setup

```bash
# install python 3.9
brew install python@3.9

# verify version is install
python3 --version

# location
which python3
# /opt/homebrew/bin/python3

### create venv to install packages
# Create directory for venvs
mkdir python_virtualenvs
cd python_virtualenvs

# create venv for all our stuff (sampythonsample)
python3 -m venv sampythonsample

# activate this env
source sampythonsample/bin/activate
source python_virtualenvs/sampythonsample/bin/activate

# or if running from other directory (sampythonsample)
source ../python_virtualenvs/sampythonsample/bin/activate
# verify python location
which python3
# xxxxxxx/python_virtualenvs/sampythonsample/bin/python3

```

## Deploy the application

To use the SAM CLI, you need the following tools.

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build the docker image run the following in your shell:

```bash
sam build
```

### Samconfig.toml
The project utilizes a sam config toml file for all common SAM deploy arguments. 

The file is configured to support multiple deployment environments (dev, tst).

```bash
# Deploy to default 'dev' environment
sam deploy

# Deploy to 'tst' environment
sam deploy --config-env tst
```

Sample samconfig.toml file sections 

```yaml
[default.deploy.parameters]
stack_name = "sam-python-sample"
parameter_overrides = [
    "S3BucketName=tjanusz-personal-demo-stuff",
    "ValidBaseImagesKey=dockerImagesSecInfo/validBaseImages.csv",
    "EnvPrefix=Dev"
]

[tst.deploy.parameters]
stack_name = "tst-sam-python-sample"
parameter_overrides = [
    "S3BucketName=tjanusz-personal-demo-stuff",
    "ValidBaseImagesKey=dockerImagesSecInfo/validBaseImages.csv",
    "EnvPrefix=Tst"
]

```

## Use the SAM CLI to build and test locally

Build your application with the `sam build` command.

```bash
sam-python-sample$ sam build
```

The SAM CLI builds a docker image from a Dockerfile and then installs dependencies defined in `ecsHelpers/requirements.txt` inside the docker image. The processed template file is saved in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is a JSON document that represents the input that the function receives from the event source. Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `sam local invoke` command.

```bash
sam-python-sample$ sam local invoke EcsReaderFunction --event events/event.json
```

## Unit tests

Tests are defined in the `tests` folder in this project. 

The tests folder has a 'requirements.txt' file with all unit testing requirements added.

```bash
# in tests directory run to install all dependencies
pip install -r requirements.txt

# run all unit tests in project
python -m pytest tests/ -v
```

## ECR Repository Info

The easiest way is to have the ECR repo setup BEFORE you do the 'sam deploy'.

In order to specify the ECR repo name you need to modify the samconfig.toml file and set the image_repository setting

```bash
[default.deploy.parameters]
# set the image repo to 
image_repository= "211287010274.dkr.ecr.us-east-1.amazonaws.com/sam-python-sample"

# if there are multiple lambdas pointing to DIFFERENT docker images use this approach
image_repositories = ["HelloWorldFunction=211287010274.dkr.ecr.us-east-1.amazonaws.com/sam-python-sample",
   "HelloWorldFunction2=211287010274.dkr.ecr.us-east-1.amazonaws.com/sam-python-sample2"]
```

## Multiple Functions in a single Docker Image
To have multiple lambda functions deployed into the same docker image follow these instructions:

* Modify the template.yaml file to have each function definition use SAME metadata but DIFFERENT docker commands
```yaml
  HelloWorldFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      ImageConfig:
        Command:
          - app.lambda_handler         <-- specific command to invoke this lambda
    Metadata:                          <-- same metadata
      Dockerfile: Dockerfile
      DockerContext: ./hello_world
      DockerTag: python3.9-v1

  HelloWorldFunction2:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      ImageConfig:
        Command:
          - app2.lambda_handler      <-- specific command to invoke this lambda
    Metadata:
      Dockerfile: Dockerfile           <-- same metadata
      DockerContext: ./hello_world
      DockerTag: python3.9-v1
```

* Also ensure all required python files are added to the single docker image w/in dockerfile!
```yaml
# use correct base python version
FROM public.ecr.aws/lambda/python:3.9

# need to ensure we copy over the correct files into the container
COPY *.py requirements.txt ./

```

## Notes/Issues
This section outlines anything specific found using SAM with docker images.

* Apparently SAM will always 'munge' the image tag (https://github.com/aws/aws-sam-cli/issues/2600) so we can't have clean images tags! This is a super huge restriction.
```bash
docker images
## this is what SAM creates
helloworldfunction-7d10b7dc0248-python3.9-v1

## this is what I want and unable to do so! Major bummer!
python3.9-v1

``` 

## Lambda Policies
This section provides some notes I found trying to use SAM policy templates.

The yaml is super touchy!! Indentation and properties must be exact if not SAM will generate invalidate template. I saw values with null etc..

```yaml
  BaseImageFinderFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Join ["-", [!Ref EnvPrefix, "sam-python-base-image-finder"]]
      Policies:
        - S3ReadPolicy:
            BucketName: !Ref S3BucketName         <-- can use Cfn parameter references
        - LambdaInvokePolicy:
            FunctionName: !Ref EcsReaderFunction  <--- super touchy here wants reference to lambda NOT actual property
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)

## TODO Items

* Add in some event bridge rules to kick off Lambda on a given interval
* Figure out how to create a policy that lets me read ECS cluster info