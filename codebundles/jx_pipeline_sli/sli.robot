*** Settings ***
Documentation       SLI for Tekton Pipelines on Jenkins X
Metadata            Author    Harsh Mishra
Metadata            Display Name    SLI for Jenkins X Pipelines (Tekton)
Metadata            Supports    Kubernetes,AKS,EKS,GKE,OpenShift,JenkinsX

Library             BuiltIn
Library             RW.Core
Library             RW.CLI
Library             OperatingSystem
Library             JXKeywords.Pipelines.PipelineInfo

Suite Setup         Suite Initialization


*** Tasks ***
Return Failing Pipeline Runs within a Given Time Interval
    [Documentation]    Returns number of failed pipeline runs in a given time interval
    [Tags]    jenkinsx pipeline health pipelineruns sli
    ${response}=    JXKeywords.Pipelines.PipelineInfo.Sli For Pipeline Runs
    ...    kubeconfig=${kubeconfig}
    ...    context=${CONTEXT}
    ...    tektonVersion=${TEKTON_API_VERSION}
    ...    namespace=${NAMESPACE}
    ...    timeInterval=${TIME_INTERVAL}

    ${total_pipeline_runs}=    Set Variable    ${response[0]}
    ${failed_pipeline_runs}=    Set Variable    ${response[1]}

    RW.Core.Debug Log    Failing Pipeline Runs: ${failed_pipeline_runs}
    RW.Core.Debug Log    Total Pipeline Runs: ${total_pipeline_runs}
    RW.Core.Push Metric    
    ...    value=${failed_pipeline_runs}
    Log    Failed Pipeline Runs: ${failed_pipeline_runs}
    Log    Total Pipeline Runs: ${total_pipeline_runs}


*** Keywords ***
Suite Initialization
    ${kubeconfig}=    RW.Core.Import Secret
    ...    kubeconfig
    ...    type=string
    ...    description=The kubernetes kubeconfig yaml containing connection configuration used to connect to cluster(s).
    ...    pattern=\w*
    ...    example=For examples, start here https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/

    ${NAMESPACE}=    RW.Core.Import User Variable    NAMESPACE
    ...    type=string
    ...    description=The name of the Kubernetes namespace to scope actions and searching to.
    ...    pattern=\w*
    ...    example=my-namespace

    ${CONTEXT}=    RW.Core.Import User Variable    CONTEXT
    ...    type=string
    ...    description=Which Kubernetes context to operate within.
    ...    pattern=\w*
    ...    example=my-main-cluster
 
    ${TIME_INTERVAL}=    RW.Core.Import User Variable    TIME_INTERVAL
    ...    type=integer
    ...    description=Time interval to measure in 
    ...    pattern=^-?\d+$
    ...    example=3600
    ...    default=86400
    
    ${TEKTON_API_VERSION}=    RW.Core.Import User Variable   TEKTON_API_VERSION
    ...    type=string
    ...    description=API Version for use in Tekton over JenkinsX.
    ...    pattern=\w*
    ...    example=v1beta1
    ...    default=v1beta1

    ${HOME}=    RW.Core.Import User Variable    HOME

    Set Suite Variable    ${kubeconfig}    ${kubeconfig}
    Set Suite Variable    ${CONTEXT}    ${CONTEXT}
    Set Suite Variable    ${NAMESPACE}    ${NAMESPACE}
    Set Suite Variable    ${HOME}    ${HOME}
    Set Suite Variable    ${TEKTON_API_VERSION}    ${TEKTON_API_VERSION}
    Set Suite Variable    ${TIME_INTERVAL}    ${TIME_INTERVAL}
    # Set Suite Variable    ${REPO}    ${REPO}