# Writing unit tests for Chalice

[Chalice](http://chalice.readthedocs.io/en/latest/api.html) is a Python serverless microframework for AWS that enables you to quickly create and deploy applications that use [Amazon API Gateway](https://aws.amazon.com/api-gateway/) and [AWS Lambda](https://aws.amazon.com/lambda/). In this blog post, I discuss how to create unit tests for Chalice and automate testing with [AWS CodeBuild](https://aws.amazon.com/codebuild/). I'll use Chalice local mode to execute these tests without provisioning API Gateway and Lambda resources.

## Creating a new project

Let's begin by creating a new Chalice project using the **chalice** command line. 

*Note: You might want to create a [virtual environment](https://virtualenv.pypa.io/en/stable/) to complete the tasks in this post.*

```
$ pip install chalice 
$ chalice new-project helloworld && cd helloworld
$ cat app.py
```

As you can see, this creates a simple application with a few sample functions. Notice that there are two functions, **hello_name** and **create_user**, which are commented out in the sample code. Open **app.py** in a text editor and uncomment those lines. The complete application should look like this.

```
from chalice import Chalice

app = Chalice(app_name='chalice-unit-test')


@app.route('/')
def index():
    return {'hello': 'world'}


@app.route('/hello/{name}')
def hello_name(name):
    # '/hello/james' -> {"hello": "james"}
    return {'hello': name}


@app.route('/users', methods=['POST'])
def create_user():
    # This is the JSON body the user sent in their POST request.
    user_as_json = app.current_request.json_body
    # We'll echo the json body back to the user in a 'user' key.
    return {'user': user_as_json}
```

## Chalice local mode

As you develop your application, you can experiment locally before deploying your changes. You can use the **chalice local** command to spin up a local HTTP server, as follows. 

```
$ chalice local
Serving on 127.0.0.1:8000
```

Now we can test our application using cURL. 

*Note: You will need to start a second shell.*

```
$ curl 127.0.0.1:8000
{"hello": "world"}
```

Local mode is great, but we want to automate testing to ensure all our tests run regularly. Next, I'll create a Python unit test to automate testing.

## Writing a unit test

**pytest** is a framework that makes it easy to write unit tests. If you don't already have **pytest** installed, you can install it using pip.

```
$ pip install pytest
```

I'll add a new module named **app_test.py** to my project, with the following content.

```
import json
import pytest
from app import app


@pytest.fixture
def gateway_factory():
    from chalice.config import Config
    from chalice.local import LocalGateway

    def create_gateway(config=None):
        if config is None:
            config = Config()
        return LocalGateway(app, config)
    return create_gateway


class TestChalice(object):

    def test_index(self, gateway_factory):
        gateway = gateway_factory()
        response = gateway.handle_request(method='GET',
                                          path='/',
                                          headers={},
                                          body='')
        assert response['statusCode'] == 200
        assert json.loads(response['body']) == dict([('hello', 'world')])
```
Let's examine the code. First, I defined a fixture named **gateway_factory**, that creates a new local gateway we can use in our test cases. This is the Python equivalent of the **chalice local** command line we ran earlier. *Note that **Config** and **LocalGateway** objects used inside the factory are private and may change in the future.* 

Next, I defined new class named **TestChalice** with a single test named **test_index**. test_index submits a GET request to our application and verifies that I receive an expected response. This is the equivalent of the **curl** command that we tested earlier. You execute the unit test with the **pytest** command. 

```
$ pytest
========================= test session starts ========================
platform linux2 -- Python 2.7.12, pytest-3.4.2, py-1.5.3, pluggy-0.6.0
rootdir: /home/ec2-user/helloworld, inifile:
plugins: pep8-1.0.6, flakes-2.0.0, cov-2.5.1
collected 1 item

app_test.py .                                                    [100%]

====================== 1 passed in 0.02 seconds ======================
```

## Adding tests

Let's add a few more tests to validate the other functions in our project. **test_hello** expects to receive a name of the person to say hello to in the path. Here is a test case that passes "alice" and ensures that the response is correct.

```
    def test_hello(self, gateway_factory):
        gateway = gateway_factory()
        response = gateway.handle_request(method='GET',
                                          path='/hello/alice',
                                          headers={},
                                          body='')
        assert response['statusCode'] == 200
        assert json.loads(response['body']) == dict([('hello', 'alice')])
```

Unlike the previous functions, **test_users** uses the POST verb instead of GET. POST requests require a body and a content-type header to tell Chalice the type of data you're sending. 

```
    def test_users(self, gateway_factory):
        gateway = gateway_factory()
        response = gateway.handle_request(method='POST',
                                          path='/users',
                                          headers={'Content-Type':
                                                   'application/json'},
                                          body='["alice","bob"]')
        assert response['statusCode'] == 200
        expected = json.loads('{"user":["alice","bob"]}')
        actual = json.loads(response['body'])
        assert actual == expected
```

Now, when we run pytest, our three tests are all run and all three pass.

```
$ pytest
========================= test session starts ========================
platform linux2 -- Python 2.7.12, pytest-3.4.2, py-1.5.3, pluggy-0.6.0
rootdir: /home/ec2-user/helloworld, inifile:
plugins: pep8-1.0.6, flakes-2.0.0, cov-2.5.1
collected 4 items

app_test.py ...                                                 [100%]

====================== 3 passed in 0.05 seconds ======================
```

Your tests can now be added to a continuous deployment (CD) pipeline. The pipeline can run tests on code changes and, if they pass, promote the new build to a testing stage. Chalice can generate a CloudFormation template that will create a starter CD pipeline. It contains a CodeCommit repo, a CodeBuild stage for packaging your chalice app, and a CodePipeline stage to deploy your application using CloudFormation. For more information see the **chalice generate-pipeline** command in the [Chalice Documentation](http://chalice.readthedocs.io/en/latest/topics/cd.html).

## Conclusion 

Using Chalice, you can quickly create and deploy serverless applications. In addition, Chalice's local mode enables you to easily create unit tests for your projects. Finally, Chalice can generate a continuous deployment to automate testing. 