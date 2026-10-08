# College Lost and Found Threat Model

Scope: Flask application, SQLite schema, browser templates, Docker Compose with Caddy TLS, and isolated kind deployment. Laboratory case study for Marisetti Avinash CH.SC.U4CYS23024. This model distinguishes implementation facts from production prerequisites. Independent architecture review was completed and its recommendations were incorporated into login throttling, invalid-host errors, pagination and closed-state feedback.

## Assets and authority
Credentials and password hashes; signed session and CSRF tokens; private message bodies; report ownership and recovery state; moderation decisions; audit metadata; database volumes; deployment secrets; source and built images. Students and faculty share campus-user authority. Only an operator provisions administrators. Administrators moderate reports and inspect audit metadata but have no general access to participant inboxes. Storage and host operators remain privileged trusted actors.

## Architecture and boundaries
Browser -> Caddy HTTPS -> Gunicorn/Flask -> private SQLite volume. Kubernetes uses app and TLS sidecar in one restricted pod with two PVCs and ClusterIP service. TB1 untrusted browser to authenticated application; TB2 application policy to persistent store; TB3 operator to secrets, deployment, backups and source. Inputs include form fields, search terms, object IDs, Host, cookies and recipient message IDs. Flask guards reload role from the database. All mutation routes validate CSRF. SQL parameters bind user input. Templates autoescape text and CSP disables script execution. Private-contact recipients derive from report ownership; inbox and reply queries enforce participants.

Source anchors: app.py:22 validation, :29 owner policy, :33 factory/configuration, :135 login, :142 atomic reservation, :175 search, :196 report, :230 recover, :243 contact, :264 inbox, :270 reply, :292 administration, :301 moderation; schema.sql for relational keys and constraints; Dockerfile, compose.yaml, deploy/kubernetes.yaml, deploy/Dockerfile.tls for runtime authority.

## STRIDE threats and controls
TH01 Spoof campus identity through credential guessing. scrypt, generic failures, dummy hash and atomic source/account attempt reservation mitigate guessing. Campus identity verification and central revocation remain future work.
TH02 Spoof administrator during registration. Student/faculty role allowlist and separate operator provisioning prevent form-based elevation.
TH03 Tamper with another report recovery state. Reporter ID policy, verified/open preconditions, CSRF and bound update reject cross-user writes.
TH04 Tamper with moderation as a normal user. Admin guard and auditable decision/reason enforce role authority.
TH05 Repudiate recovery or moderation. UTC actor/object/outcome audit metadata supports accountability; separate immutable audit export is a production prerequisite.
TH06 Disclose private messages by guessing IDs. Participant-only inbox and recipient-only reply policy block unrelated users, including administrators.
TH07 Disclose credentials through public views or logs. Public queries omit emails/hashes; audit omits passwords and message bodies; secrets stay outside image/source.
TH08 Inject active content in reports/messages. Bounded validation, escaped templates, restrictive CSP and no upload feature reduce content execution.
TH09 Inject SQL through search or IDs. Fixed SQL structure and bound parameters enforce separation.
TH10 Deny service with large requests or repeated sends. 16 KiB body bound, bounded fields and transactional per-sender message rate caps mitigate abuse; containers have resource limits.
TH11 Elevate container privilege. Non-root UID10001, read-only rootfs, no-new-privileges, dropped capabilities, RuntimeDefault seccomp and restricted namespace limit runtime authority.
TH12 Compromise delivery through vulnerable dependencies or secret commits. Patched hash-locked dependencies, dependency audit, static checks, ignored secret files and pinned base digests support delivery integrity. Hosted branch protection is a planned remote setting, not an observed control.

## Sensitive flows
Credentials flow only through validated TLS sign-in and scrypt comparison to the private user store. Message body flows only to sender and derived recipient; metadata-only audits omit body. Recovery decisions flow from authenticated reporter through ownership and state checks into report storage and audit.

## Attack tree
Goal: unauthorized recovery (OR). Branch A: obtain reporter credential/session AND authenticate as reporter. Branch B: choose victim report ID AND defeat owner policy. Branch C: gain operator/storage authority AND issue direct database write. Preventive controls are TLS/hash/session policy, CSRF/ownership/bound SQL, and host RBAC/private volumes. Detective controls are login/recovery-denial events and future external audit integrity checks.

## Validation and residual risk
34 unit, integration, system and fuzz tests passed. Actual browser workflow passed. Docker and Kubernetes authenticated workflows passed over TLSv1.3 with local-CA certificate and localhost hostname validation. Default kind networking does not prove NetworkPolicy enforcement. SQLite remains a single-node store; at-rest encryption, encrypted backups, immutable audit export, campus SSO, central revocation, trusted campus TLS and capacity validation are required before production use. Initial insecure refactoring examples are nonexecuted teaching snippets, not claimed deployed exploits. Nominal sprint durations are plans and Jira transitions are compressed lab evidence.
