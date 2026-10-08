# Security invariants

- Only the authenticated report creator may mark an open verified report recovered.
- Only a provisioned administrator may verify or remove reports. Self-registration allows student/faculty only.
- Pending or removed reports are visible only to their creator and administrators.
- Private conversations are available only to their participants. Administrative report access does not grant blanket inbox access.
- All mutation routes validate a session-bound CSRF token. User-supplied identifiers must not determine authority.
- Database values are bound parameters; rendered report/message content remains escaped.
- Secret values, passwords and private message bodies must not enter source, submission packages or audit events.

The lab trusts the local deployment operator. Direct operator access to a database or volume is existing privileged authority, not evidence of a remote application exploit. Campus membership verification, central session revocation, independently immutable logging, encrypted backups and campus-scale availability remain production work.

Report a suspected problem with its concrete entry point, starting privilege, new unauthorized capability and reproduction/evidence. Do not claim generic scanner patterns or configuration labels as confirmed exploitation.
