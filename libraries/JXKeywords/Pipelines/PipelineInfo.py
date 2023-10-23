import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import List, Tuple

KUBECONFIG = os.getenv("KUBECONFIG")


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
    kubeconfig=KUBECONFIG, namespace="jx", context="sandbox-cluster-1", tektonVersion="v1beta1"
) -> Tuple:
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