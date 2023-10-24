import os, logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import List, Tuple
from RW import platform
from datetime import datetime, timedelta

KUBECONFIG = os.getenv("KUBECONFIG")
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

            response = [(run["metadata"]["name"], run["status"]["conditions"][0]["status"], run["metadata"]["creationTimestamp"]) for run in pipelineRuns]

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
                (run["metadata"]["name"], run["status"]["conditions"][0]["status"], run["metadata"]["creationTimestamp"])
                for run in pipelineRuns
                if run["status"]["conditions"][0]["status"] == "False"
            ]

            return response

        except ApiException as Error:
            return []


def sli_for_pipeline_runs(
    kubeconfig=KUBECONFIG, namespace:str="jx", context:str="sandbox-cluster-1", tektonVersion:str="v1beta1", timeInterval:str="86400"
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
        item for item in PipelineRunObject.get_pipeline_runs()
        if datetime.strptime(item[2], "%Y-%m-%dT%H:%M:%SZ") >= x_seconds_ago
    ]
    failed_runs = [
        item for item in PipelineRunObject.get_failed_pipeline_runs()
        if datetime.strptime(item[2], "%Y-%m-%dT%H:%M:%SZ") >= x_seconds_ago
 
    ]
    total_pipeline_runs = len(total_runs)
    failed_pipeline_runs = len(failed_runs)
    if type(kubeconfig) == platform.Secret:
        os.remove(f"./{kubeconfig.key}")
    if total_pipeline_runs == 0:
        return (0, 0)

    return (total_pipeline_runs, failed_pipeline_runs)


# if __name__ == '__main__' :
#     print(sli_for_pipeline_runs())
