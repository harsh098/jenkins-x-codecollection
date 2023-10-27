*** Settings ***
Documentation       Check JenkinsX Pipeline Issues
Metadata            Author    Harsh Mishra
Metadata            Display Name    JenkinsX Pipeline Logs
Metadata            Supports    Kubernetes,AKS,EKS,GKE,OpenShift,JenkinsX

Library             BuiltIn
Library             RW.Core
Library             RW.CLI
Library             OperatingSystem
Library             JXKeywords.Pipelines.PipelineInfo

Suite Setup         Suite Initialization


*** Tasks ***
Get Logs of Latest Build
    [Documentation]    Fetches logs for the latest Jenkins X Build
    [Tags]    jenkinsx pipeline log logs
    # ...    target_service=${kubectl}
    ${pipeline}=    RW.CLI.Run Cli
    ...    cmd=${KUBERNETES_DISTRIBUTION_BINARY} get pipelineruns --no-headers -n ${NAMESPACE} --sort-by='.metadata.creationTimestamp' --context=${CONTEXT} | awk '{print $1}' | tail -n 1
    ...    env=${env}
    ...    secret_file__kubeconfig=${kubeconfig}
    ...    include_in_history=false

    # ...    target_service=${kubectl}
    ${logs}=    RW.CLI.Run Cli
    ...    cmd=for pod in $( ${KUBERNETES_DISTRIBUTION_BINARY} get pipelineruns $(${KUBERNETES_DISTRIBUTION_BINARY} get pipelineruns --no-headers -n ${NAMESPACE} --sort-by='.metadata.creationTimestamp' --context=${CONTEXT} | awk '{print $1}' | tail -n 1) -n ${NAMESPACE} -o json --context=${CONTEXT} | jq -r '.status.taskRuns| .[] | .status.podName');do ${KUBERNETES_DISTRIBUTION_BINARY} get pod $pod -n ${NAMESPACE} --context=${CONTEXT} &>/dev/null && ${KUBERNETES_DISTRIBUTION_BINARY} logs pod/$pod -n ${NAMESPACE} --all-containers --ignore-errors --context=${CONTEXT} || echo -e "Containers Exited"; done
    ...    env=${env}
    ...    secret_file__kubeconfig=${kubeconfig}
    ...    render_in_commandlist=true

    ${history}=    RW.CLI.Pop Shell History
    RW.Core.Add Pre To Report
    ...    Recent logs from JenkinsX Pipeline Run ${pipeline.stdout} in ${NAMESPACE}:\n\n${logs.stdout}
    RW.Core.Add Pre To Report    Commands Used:\n ${history}

Get Logs of Failing Builds
    [Documentation]    Fetches Logs of Failing Steps in Failing Builds
    [Tags]    jenkinsx pipeline log logs
    ${report}=    JXKeywords.Pipelines.PipelineInfo.Get Failing Steps In Failed Builds
    ...    kubeconfig=${kubeconfig}
    ...    namespace=${NAMESPACE}
    ...    tektonVersion=${TEKTON_API_VERSION}
    ...    context=${CONTEXT}
    ...    timeInterval=${TIME_INTERVAL}
    ...    env=${env}
    ${time_total}=    Convert To Integer    ${TIME_INTERVAL}
    ${time_days}=    Evaluate    ${time_total}//86400
    ${time_hours}=    Evaluate    (${time_total}%86400)//3600
    ${time_minutes}=    Evaluate    ((${time_total}%86400)%3600)//60
    ${time_seconds}=    Evaluate    ((${time_total}%86400)%3600)%60
    RW.Core.Add Pre To Report
    ...    Failing Pipeline Runs in Last ${time_days} Days, ${time_hours} Hours, ${time_minutes} Minutes, ${time_seconds} Seconds
    RW.Core.Add Pre To Report    ${report}


*** Keywords ***
Suite Initialization
    ${kubeconfig}=    RW.Core.Import Secret
    ...    kubeconfig
    ...    type=string
    ...    description=The kubernetes kubeconfig yaml containing connection configuration used to connect to cluster(s).
    ...    pattern=\w*
    ...    example=For examples, start here https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/

    #    TODO: Add support for dedicated CLI services in future
    # ${kubectl}=    RW.Core.Import Service    kubectl
    # ...    description=The location service used to interpret shell commands.
    # ...    default=kubectl-service.shared
    # ...    example=kubectl-service.shared

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

    ${TIME_INTERVAL}=    RW.Core.Import User Variable    TIME_INTERVAL
    ...    type=string
    ...    description=Time interval (seconds) to measure in Range 1 to 604800 both included
    ...    pattern=^(?!0\d*$)(?![7-9]\d{5}$)\d{1,6}$
    ...    example=3600
    ...    default=86400

    ${TEKTON_API_VERSION}=    RW.Core.Import User Variable    TEKTON_API_VERSION
    ...    type=string
    ...    description=API Version for use in Tekton over JenkinsX.
    ...    pattern=\w*
    ...    example=v1beta1
    ...    default=v1beta1

    #    TODO: Add Support for jx cli binary in future tasks
    # ${JX_BINARY}=    RW.Core.Import User Variable    JX_BINARY
    # ...    type=string
    # ...    description=Path to jx binary for JX CLI Commands
    # ...    default=jx

    ${HOME}=    RW.Core.Import User Variable    HOME

    Set Suite Variable    ${kubeconfig}    ${kubeconfig}
    # Set Suite Variable    ${kubectl}    ${kubectl}
    Set Suite Variable    ${KUBERNETES_DISTRIBUTION_BINARY}    ${KUBERNETES_DISTRIBUTION_BINARY}
    Set Suite Variable    ${CONTEXT}    ${CONTEXT}
    Set Suite Variable    ${NAMESPACE}    ${NAMESPACE}
    Set Suite Variable    ${HOME}    ${HOME}
    Set Suite Variable    ${TEKTON_API_VERSION}    ${TEKTON_API_VERSION}
    Set Suite Variable    ${TIME_INTERVAL}    ${TIME_INTERVAL}
    # Set Suite Variable    ${REPO}    ${REPO}
    Set Suite Variable
    ...    ${env}
    ...    {"KUBECONFIG":"./${kubeconfig.key}", "KUBERNETES_DISTRIBUTION_BINARY":"${KUBERNETES_DISTRIBUTION_BINARY}", "CONTEXT":"${CONTEXT}", "NAMESPACE":"${NAMESPACE}", "HOME":"${HOME}", "TEKTON_API_VERSION":"${TEKTON_API_VERSION}", "TIME_INTERVAL":"${TIME_INTERVAL}"}
