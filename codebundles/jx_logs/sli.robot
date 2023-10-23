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
Check Health Score for Pipelines in Jenkins X
    [Documentation]    Calculates A Score between 0 and 1 for the Tekton Pipelines on Jenkins X.
    [Tags]    jenkinsx pipeline health pipelineruns sli
    ${response}=    JXKeywords.Pipelines.PipelineInfo.Sli For Pipeline Runs
    ...    kubeconfig=${kubeconfig}
    ...    context=${CONTEXT}
    ...    tektonVersion=${TEKTON_API_VERSION}
    ...    namespace=${NAMESPACE}

    ${score}=    Set Variable    ${response[0]}
    ${total_pipeline_runs}=    Set Variable    ${response[1]}
    ${failed_pipeline_runs}=    Set Variable    ${response[2]}

    RW.Core.Debug Log    Calculated Score: ${score}
    RW.Core.Debug Log    Failing Pipeline Runs: ${failed_pipeline_runs}
    RW.Core.Debug Log    Total Pipeline Runs: ${total_pipeline_runs}
    RW.Core.Push Metric    
    ...    value=${score}
    ...    metric_type=Ratio


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
 
    ${KUBERNETES_DISTRIBUTION_BINARY}=    RW.Core.Import User Variable    KUBERNETES_DISTRIBUTION_BINARY
    ...    type=string
    ...    description=Which binary to use for Kubernetes CLI commands.
    ...    enum=[kubectl,oc]
    ...    example=kubectl
    ...    default=kubectl
    
    ${TEKTON_API_VERSION}=    RW.Core.Import User Variable   TEKTON_API_VERSION
    ...    type=string
    ...    description=API Version for use in Tekton over JenkinsX.
    ...    pattern=\w*
    ...    example=v1beta1
    ...    default=v1beta1

    ${HOME}=    RW.Core.Import User Variable    HOME

    Set Suite Variable    ${kubeconfig}    ${kubeconfig}
    # Set Suite Variable    ${kubectl}    ${kubectl}
    Set Suite Variable    ${KUBERNETES_DISTRIBUTION_BINARY}    ${KUBERNETES_DISTRIBUTION_BINARY}
    Set Suite Variable    ${CONTEXT}    ${CONTEXT}
    Set Suite Variable    ${NAMESPACE}    ${NAMESPACE}
    Set Suite Variable    ${HOME}    ${HOME}
    Set Suite Variable    ${TEKTON_API_VERSION}    ${TEKTON_API_VERSION}
    Set Suite Variable    ${KUBECONFIG}    ./${kubeconfig.key}
    # Set Suite Variable    ${REPO}    ${REPO}