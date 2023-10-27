import os, logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import List, Tuple
from RW import platform
from RW.CLI import run_cli
from datetime import datetime, timedelta

KUBECONFIG = os.getenv("KUBECONFIG", default="")
logger = logging.getLogger(__name__)


class PipelineRun:
    def __init__(self, kubeconfig=KUBECONFIG, tektonVersion="v1beta1", namespace="jx", context="sandbox-cluster-1"):
        self._kubeconfig = kubeconfig
        self._namespace = namespace
        self._context = context
        config.load_kube_config(config_file=self._kubeconfig, context=self._context)
        self.customApi = client.CustomObjectsApi()
        self.tektonVersion = tektonVersion

    @property
    def namespace(self) -> str:
        return self._namespace

    @namespace.setter
    def namespace(self, namespace: str):
        self._namespace = namespace

    @property
    def kubeconfig(self) -> str:
        return self._kubeconfig

    @kubeconfig.setter
    def kubeconfig(self, path: str):
        self._kubeconfig = path
        config.load_kube_config(config_file=path)
        self.customApi = client.CustomObjectsApi()

    @property
    def context(self) -> str:
        return self._context

    @context.setter
    def context(self, context: str):
        self._context = context
        config.load_kube_config(config_file=self._kubeconfig, context=self._context)
        self.customApi = client.CustomObjectsApi()

    def get_pipeline_runs(self, **kwargs) -> List:
        try:
            pipelineRuns = self.customApi.list_namespaced_custom_object(
                "tekton.dev", version=self.tektonVersion, namespace=self._namespace, plural="pipelineruns", **kwargs
            )["items"]

            response = [
                (
                    run["metadata"]["name"],
                    run["status"]["conditions"][0]["status"],
                    run["metadata"]["creationTimestamp"],
                )
                for run in pipelineRuns
            ]

            return response

        except ApiException as Error:
            return []

    def get_failed_pipeline_runs(self, **kwargs):
        try:
            pipelineRuns = self.customApi.list_namespaced_custom_object(
                "tekton.dev", version=self.tektonVersion, namespace=self._namespace, plural="pipelineruns", **kwargs
            )["items"]

            if len(pipelineRuns) == 0:
                return []
            response = [
                (
                    run["metadata"]["name"],
                    run["status"]["conditions"][0]["status"],
                    run["metadata"]["creationTimestamp"],
                )
                for run in pipelineRuns
                if run["status"]["conditions"][0]["status"] == "False"
            ]

            return response

        except ApiException as Error:
            return []

    def get_build_pods_and_steps_from_pipeline_run_name(self, pipelineRunName: str):
        try:
            pipelineRunWrapper = self.customApi.get_namespaced_custom_object(
                "tekton.dev",
                version=self.tektonVersion,
                namespace=self._namespace,
                plural="pipelineruns",
                name=pipelineRunName,
            )
            taskRuns = pipelineRunWrapper["status"]["taskRuns"]
            response = [
                (taskRun["pipelineTaskName"], taskRun["status"]["podName"], taskRun["status"]["steps"])
                for _, taskRun in taskRuns.items()
            ]
            return response
        except ApiException as Error:
            return None


def sli_for_pipeline_runs(
    kubeconfig=KUBECONFIG,
    namespace: str = "jx",
    context: str = "sandbox-cluster-1",
    tektonVersion: str = "v1beta1",
    timeInterval: str = "86400",
) -> Tuple:
    global logger
    kubeconfig_location = kubeconfig

    if timeInterval.isdigit():
        timeInterval = int(timeInterval)
    else:
        logger.fatal("Time difference must be numeric")
        raise TypeError

    if type(kubeconfig) == platform.Secret:
        with open(f"./{kubeconfig.key}", "w") as f:
            f.write(kubeconfig.value)
            logger.info(msg="CREATING SECRET FILE")
        kubeconfig_location = f"./{kubeconfig.key}"

    x_seconds_ago = datetime.now() - timedelta(seconds=timeInterval)

    PipelineRunObject = PipelineRun(
        kubeconfig=kubeconfig_location, tektonVersion=tektonVersion, context=context, namespace=namespace
    )

    total_runs = [
        item
        for item in PipelineRunObject.get_pipeline_runs()
        if datetime.strptime(item[2], "%Y-%m-%dT%H:%M:%SZ") >= x_seconds_ago
    ]
    failed_runs = [
        item
        for item in PipelineRunObject.get_failed_pipeline_runs()
        if datetime.strptime(item[2], "%Y-%m-%dT%H:%M:%SZ") >= x_seconds_ago
    ]
    total_pipeline_runs = len(total_runs)
    failed_pipeline_runs = len(failed_runs)
    if type(kubeconfig) == platform.Secret:
        os.remove(f"./{kubeconfig.key}")
    if total_pipeline_runs == 0:
        return (0, 0)

    return (total_pipeline_runs, failed_pipeline_runs)


def _get_pod_logs(
    podName: str,
    container: str,
    kubeconfig=KUBECONFIG,
    namespace: str = "jx",
    context: str = "sandbox-cluster-1",
    env: dict = None,
):
    cmd = "".join(
        [
            "${KUBERNETES_DISTRIBUTION_BINARY}  ",
            f" --context={context} logs -n {namespace} pod/{podName} -c {container} 2> /dev/null || echo 'Containers Exited'",
        ]
    )
    output: str
    if type(kubeconfig) == platform.Secret:
        output = run_cli(
            cmd=cmd, 
            env=env, 
            secret_file__kubeconfig=kubeconfig
        )
    else:
        output = run_cli(
            cmd=cmd,
            env=env,
        )

    return output.stdout


def _generate_report(fail_report):
    body = []

    for taskRun in fail_report["taskRuns"]:
        steps = []
        for step in taskRun["failedSteps"]:
            stepObject = f"""
                Step Name : {step["name"]}
                Container Name: {step["containerName"]}
                Logs :
                -----------------------------------------------------
                {step["logs"]}
                -----------------------------------------------------
            """
            steps.append(stepObject)
        stepsReport = "\n".join(steps)
        taskReport = f"""
            Task Run Name : {taskRun["taskRunName"]}
            Logging Pod : {taskRun["podName"]}

            Failing Steps:
            {stepsReport} 
        """
        body.append(taskReport)

    response_body = "\n".join(body)
    report = f"""
        ________________________________________________________________
        Pipeline Run : {fail_report["failedPipelineRunName"]}
        Creation Timestamp: {fail_report["creationTimestamp"]}
        {response_body}

        ________________________________________________________________
    """
    return report


def get_failing_steps_in_failed_builds(
    kubeconfig=KUBECONFIG,
    namespace: str = "jx",
    context: str = "sandbox-cluster-1",
    tektonVersion: str = "v1beta1",
    timeInterval: str = "86400",
    env: dict = None,
):
    global logger
    kubeconfig_location = kubeconfig

    if timeInterval.isdigit():
        timeInterval = int(timeInterval)
    else:
        logger.fatal("Time difference must be numeric")
        raise TypeError

    if type(kubeconfig) == platform.Secret:
        with open(f"./{kubeconfig.key}", "w") as f:
            f.write(kubeconfig.value)
            logger.info(msg="CREATING SECRET FILE")
        kubeconfig_location = f"./{kubeconfig.key}"

    x_seconds_ago = datetime.now() - timedelta(seconds=timeInterval)

    PipelineRunObject = PipelineRun(
        kubeconfig=kubeconfig_location, tektonVersion=tektonVersion, context=context, namespace=namespace
    )

    failed_runs = [
        item
        for item in PipelineRunObject.get_failed_pipeline_runs()
        if datetime.strptime(item[2], "%Y-%m-%dT%H:%M:%SZ") >= x_seconds_ago
    ]

    failed_steps = []
    for run in failed_runs:
        failed_run_name = run[0]
        failed_timestamp = run[2]
        build_pods_and_steps_from_pipeline_run_name = PipelineRunObject.get_build_pods_and_steps_from_pipeline_run_name(
            failed_run_name
        )
        run_failed_steps = []
        try:
            for taskName, podName, steps in build_pods_and_steps_from_pipeline_run_name:
                task_failed_steps = [
                    {
                        "name": step["name"],
                        "containerName": step["container"],
                        "logs": _get_pod_logs(
                            podName=podName,
                            container=step["container"],
                            kubeconfig=kubeconfig_location,
                            namespace=namespace,
                            env=env,
                            context=context,
                        ),
                    }
                    for step in steps
                    if step["terminated"]["exitCode"] != 0
                ]
                info = {"taskRunName": taskName, "podName": podName, "failedSteps": task_failed_steps}
                run_failed_steps.append(info)
            info = {
                "failedPipelineRunName": failed_run_name,
                "creationTimestamp": failed_timestamp,
                "taskRuns": run_failed_steps,
            }
            failed_steps.append(info)
        except KeyError as k:
            # Skipping Pending pipelines as of noe
            # TODO: Add support for Failed pipelines with Pending Status
            continue

    if type(kubeconfig) == platform.Secret:
        os.remove(f"./{kubeconfig.key}")

    reports = []
    for step in failed_steps:
        reports.append(_generate_report(step))

    final_report = "\n".join(reports)

    return final_report
