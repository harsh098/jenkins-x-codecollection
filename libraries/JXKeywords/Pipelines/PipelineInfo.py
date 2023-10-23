import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import List, Tuple
from RW import platform

KUBECONFIG = os.getenv("KUBECONFIG")
SECRET_PREFIX = "secret__"
SECRET_FILE_PREFIX = "secret_file__"


def _create_secrets_from_kwargs(**kwargs) -> list[platform.ShellServiceRequestSecret]:
    """Helper to organize dynamically set secrets in a kwargs list

    Returns:
        list[platform.ShellServiceRequestSecret]: secrets objects in list form.
    """
    global SECRET_PREFIX
    global SECRET_FILE_PREFIX
    request_secrets: list[platform.ShellServiceRequestSecret] = [] if len(kwargs.keys()) > 0 else None
    for key, value in kwargs.items():
        if not key.startswith(SECRET_PREFIX) and not key.startswith(SECRET_FILE_PREFIX):
            continue
        if not isinstance(value, platform.Secret):
            logger.warning(f"kwarg secret {value} in key {key} is the wrong type, should be platform.Secret")
            continue
        if key.startswith(SECRET_PREFIX):
            request_secrets.append(platform.ShellServiceRequestSecret(value))
        elif key.startswith(SECRET_FILE_PREFIX):
            request_secrets.append(platform.ShellServiceRequestSecret(value, as_file=True))
    return request_secrets


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

    def get_pipeline_runs(self) -> List:
        try:
            pipelineRuns = self.customApi.list_namespaced_custom_object(
                "tekton.dev", version=self.tektonVersion, namespace=self._namespace, plural="pipelineruns"
            )["items"]

            response = [(run["metadata"]["name"], run["status"]["conditions"][0]["status"]) for run in pipelineRuns]

            return response

        except ApiException as Error:
            return []

    def get_failed_pipeline_runs(self):
        try:
            pipelineRuns = self.customApi.list_namespaced_custom_object(
                "tekton.dev", version=self.tektonVersion, namespace=self._namespace, plural="pipelineruns"
            )["items"]

            response = [
                (run["metadata"]["name"], run["status"]["conditions"][0]["status"])
                for run in pipelineRuns
                if run["status"]["conditions"][0]["status"] == "False"
            ]

            return response

        except ApiException as Error:
            return []


def sli_for_pipeline_runs(
    kubeconfig=KUBECONFIG, namespace="jx", context="sandbox-cluster-1", tektonVersion="v1beta1", **kwargs
) -> Tuple:
    request_secrets=_create_secrets_from_kwargs(**kwargs)
    PipelineRunObject = PipelineRun(
        kubeconfig=kubeconfig, tektonVersion=tektonVersion, context=context, namespace=namespace
    )
    total_pipeline_runs = len(PipelineRunObject.get_pipeline_runs())
    if total_pipeline_runs == 0:
        return (0.0, 0, 0)

    failed_pipeline_runs = len(PipelineRunObject.get_failed_pipeline_runs())

    return (round(1 - (failed_pipeline_runs / total_pipeline_runs), 1), total_pipeline_runs, failed_pipeline_runs)


# if __name__ == '__main__' :
#     sli_for_pipeline_runs()