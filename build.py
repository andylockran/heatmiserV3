from pybuilder.core import task, init

@init
def initialise(project):
    pass

@task
def hello_world():
    print("Hello, world!")