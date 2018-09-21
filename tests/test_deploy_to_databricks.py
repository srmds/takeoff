import unittest

from sdh_deployment.deploy_to_databricks import JobConfig, DeployToDatabricks as victim

jobs = [
    JobConfig("foo-SNAPSHOT", 1),
    JobConfig("bar-0.3.1", 2),
    JobConfig("foobar-0.0.2", 3),
    JobConfig("barfoo-0.0.2", 4),
    JobConfig("baz-0e12f6d", 5),
]

streaming_job_config = "tests/test_job_config.json.j2"
batch_job_config = "tests/test_job_config_scheduled.json.j2"


class TestDeployToDatabricks(unittest.TestCase):
    def test_find_application_job_id_if_snapshot(self):
        assert victim._application_job_id("foo", jobs) == 1

    def test_find_application_job_id_if_version(self):
        assert victim._application_job_id("bar", jobs) == 2

    def test_find_application_job_id_if_hash(self):
        assert victim._application_job_id("baz", jobs) == 5

    def test_is_streaming_job(self):
        job_config = victim._construct_job_config(
            config_file_fn=streaming_job_config,
            name="app",
            version="42",
            egg="some.egg",
            python_file="some.py",
        )
        assert victim._job_is_streaming(job_config) is True

        job_config = victim._construct_job_config(
            config_file_fn=batch_job_config,
            name="app",
            version="42",
            egg="some.egg",
            python_file="some.py",
        )
        assert victim._job_is_streaming(job_config) is False

    def test_construct_job_config(self):
        job_config = victim._construct_job_config(
            config_file_fn=streaming_job_config,
            name="app",
            version="42",
            egg="some.egg",
            python_file="some.py",
        )

        assert {
            "name": "app-42",
            "libraries": [
               {"egg": "some.egg"},
               {"jar": "some.jar"}
            ],
            "new_cluster": {
                "spark_version": "4.1.x-scala2.11",
                "spark_conf": {
                    "spark.sql.warehouse.dir": "/some_",
                    "some.setting": "true",
                },
                "cluster_log_conf": {"dbfs": {"destination": "dbfs:/mnt/sdh/logs/app"}},
            },
            "some_int": 5,
            "spark_python_task": {"python_file": "some.py"}} == job_config
