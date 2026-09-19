{{- define "changeguard.name" -}}changeguard{{- end }}
{{- define "changeguard.labels" -}}
app.kubernetes.io/name: {{ include "changeguard.name" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
