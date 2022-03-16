FROM public.ecr.aws/lambda/python:3.9

# need to ensure we copy over the correct files into the container
COPY *.py requirements.txt ./

RUN python3.9 -m pip install -r requirements.txt -t .

# Command can be overwritten by providing a different command in the template directly.
CMD ["ecs_reader.lambda_handler"]
