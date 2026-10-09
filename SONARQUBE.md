# SonarQube analysis for College Lost and Found

This project uses your preserved SonarQube installation copied to `D:\sse\.tools\sonarqube-26.6.0.123539`. Its original installation at `C:\Users\NAANI\Music\sonarqube-26.6.0.123539` is retained as a stopped backup. The server stores results; the separate official SonarScanner for Python uploads analysis. The project key is `College-Lost-and-Found`.

## Start the existing server

Run `D:\sse\.tools\sonarqube-26.6.0.123539\bin\windows-x86-64\StartSonar.bat`, then open http://localhost:9000. Windows blocks the downloaded batch launcher when started automatically. Review its Properties and provenance before choosing Unblock yourself. Keep the server running. Existing SonarQube login credentials are separate from the website demo accounts and Jira credentials. Do not start the C: and D: installations together on the same ports.

## Indexing failure and preserved relocation

Task `3215850b-4adb-48cc-822b-90ea3fbd9c2d` uploaded successfully but failed during server indexing. `ce.log` and `es.log` identify the cause: C: exceeded the 95% flood-stage watermark, so Elasticsearch marked its indexes read-only. Approximately 3% of C: was free, while D: had approximately 90 GiB free. After you stopped the server gracefully, the existing program and data were copied to D:. The copied `sonar.mv.db` SHA256 matched the original before startup. No user files or indexes were deleted and disk protection was not disabled. SonarQube now needs to be launched from the D: copy so its default `data` path uses that drive.

The yellow embedded-H2-database banner is a separate warning: H2 is suitable for this local evaluation, but a durable production service needs a supported external database. It is not the cause of the failed indexing task. Changing databases is a separate migration and is not needed to fix this laboratory failure.

Verify readiness in PowerShell:

```powershell
Invoke-RestMethod 'http://localhost:9000/api/system/status'
```

Expect `status: UP`; startup is not complete while it says STARTING. Check the installation's `logs\sonar.log`, `web.log` and `es.log` if startup fails.

## Scanner installation and verification

An isolated environment is prepared under `.tools\sonar-venv`; it does not change the application's dependencies. To recreate it:

```powershell
Set-Location D:\sse
$sonarPython = 'C:\Users\NAANI\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $sonarPython -m venv .tools\sonar-venv
& .\.tools\sonar-venv\Scripts\python.exe -m pip install 'pysonar==1.8.0.5390' coverage -r requirements.txt
& .\.tools\sonar-venv\Scripts\python.exe -c "from importlib.metadata import version; print('Official pysonar scanner ' + version('pysonar'))"
& .\.tools\sonar-venv\Scripts\pysonar.exe --help
```

Generate real coverage from the project's tests without uploading:

```powershell
& .\scripts\sonar-scan.ps1 -PrepareOnly
```

This must pass tests and create `.sonar-evidence\coverage.xml`. The scanner imports this file; it does not run tests itself. Coverage focuses on `app.py`; orchestration scripts and the WSGI entry point are analyzed but excluded from the coverage denominator.

## Create the project and analysis token

In SonarQube, create a local project with key `College-Lost-and-Found`, name `College Lost and Found 20CYS401`, and main branch `main`. Choose a new-code definition appropriate to this initial lab baseline. Under My Account → Security, generate a project analysis token for that project. The token needs Execute Analysis permission; use a separate read-capable token if your project permissions require one to query issues. Never use the Jira token.

Enter the token without saving it in a file or putting it in command history:

```powershell
$sonarTokenInput = Read-Host 'SonarQube analysis token' -AsSecureString
$sonarTokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sonarTokenInput)
try {
    $env:SONAR_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($sonarTokenPointer)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($sonarTokenPointer)
}
try {
    & .\scripts\sonar-scan.ps1
} finally {
    Remove-Item Env:SONAR_TOKEN -ErrorAction SilentlyContinue
}
```

Do not enable scanner debug output when sharing logs. Runtime secrets, database data, generated reports and downloaded tools are outside the configured source paths. The scanner analyzes the application, templates, stylesheet, deployment configuration and scripts, with tests indexed separately.

## Verify the upload and inspect findings

1. Open http://localhost:9000/dashboard?id=College-Lost-and-Found. Confirm the project and last-analysis time match this run.
2. Check `.sonar-evidence\scanner.log` for successful analysis submission and `.sonar-evidence\report-task.txt` for the background task ID and dashboard URL. A submitted task alone is not proof that server processing succeeded. In Project Settings → Background Tasks, confirm the latest task succeeded.
3. The runner waits for the quality gate. A failing gate produces a nonzero exit even when upload succeeded. Read the individual gate conditions, including coverage, duplication and security review; do not describe a failed gate as a failed upload.
4. Review both Overall Code and New Code. Open Issues and filter the Security software quality or Vulnerability type, according to the UI mode. Also inspect Reliability and Maintainability issues. Each finding links to a rule and affected source location.
5. Open Security Hotspots. Read the rule's risk, sensitive code and recommended controls. A hotspot requires contextual review and is not automatically an exploitable vulnerability. Mark it Safe only after reviewing why the existing code is safe, or Fixed after an appropriate change. Record the evidence in the review comment.

## Demonstrate a security fix

While `SONAR_TOKEN` is set, preserve the actual server results with:

```powershell
& .\scripts\sonar-results.ps1 -Label before
# Make a justified fix, rerun tests and upload a new scan.
& .\scripts\sonar-scan.ps1
& .\scripts\sonar-results.ps1 -Label after
```

Snapshots are saved in `.sonar-evidence\before-results.json` and `after-results.json` with analysis IDs, gate conditions, metrics, paginated issues and hotspots. This requires project Browse permission in addition to the analysis permission. Use the instance's `/web_api` documentation if an endpoint changes in your installed version.

## Why the application has separate roles

The application has student, faculty and administrator roles, not student faculty and teacher. Teacher is an ordinary synonym for faculty here. Students and faculty have identical lost-and-found permissions; the distinction records their campus user class. Both could be represented by one campus-user permission group, as the use-case diagram already shows. Administrator is the necessary separate privilege: the assigned problem explicitly requires administrators to verify or remove suspicious reports. Giving every user one shared administrator role would allow users to approve or remove others' reports. In all roles, recovery remains restricted to the report creator, and private messaging remains restricted to conversation participants. An administrator does not receive blanket access to private inboxes.

Record the issue key, rule, file, line, analysis timestamp and reason the finding matters. Reproduce the relevant behavior in an isolated test. Apply a justified fix and add or update a meaningful regression test. Run the same scanner command with the same project key, scope and quality profile. Verify that server processing succeeded and the issue is resolved in the later analysis; preserve the before/after analysis IDs and test evidence. Review remaining hotspots separately. Do not hide an issue with exclusions or mark it false positive solely to make the gate green.

The report's initial insecure examples are nonexecuted teaching text. This scan assesses the current source, so it cannot prove those historical fixes by itself. A legitimate historical comparison needs a separate isolated checkout of the actual earlier source, never a vulnerable deployment or edits that weaken the working app.

SonarQube is static analysis, not a complete security guarantee. Retain the existing dependency audit and authorization/CSRF/private-message tests. A zero-finding result does not prove the absence of business-logic vulnerabilities; dependency scanning capabilities vary by installed edition.

## Official references

- [SonarScanner for Python](https://docs.sonarsource.com/sonarqube-community-build/analyzing-source-code/scanners/sonarscanner-for-python)
- [Python coverage import](https://docs.sonarsource.com/sonarqube-community-build/analyzing-source-code/test-coverage/python-test-coverage)
- [Security hotspots](https://docs.sonarsource.com/sonarqube-community-build/user-guide/security-hotspots)
