for pod in $(kubectl get pipelinerun $(kubectl get pipelineruns --no-headers -n jx --sort-by='.metadata.creationTimestamp'| awk '{print $1}' | tail -n 1) -n jx -o json | jq -r '.status.taskRuns| .[] | .status.podName');do kubectl get pod $pod -n jx &>/dev/null && kubectl logs pod/$pod -n jx --all-containers --ignore-errors || echo -e "Containers Exited"; done