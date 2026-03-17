# Lifecycle Matrix

| Phase | Action | Key Impact | Notes |
|---|---|---|---|
| Signup | Generate UVK + User Key | User keys created | User key persisted server-side |
| Login | Fetch vault + unlock | UVK unwrap | Device vault register if missing |
| Invite | Pre-provision CHK wrap | Wrap stored server-side | Invite != access |
| Accept | Wrap returned | CHK unwrap | Accept = access |
| Message send | MLS + CHK encrypt | Live + storage | Dual encryption |
| Leave/remove | Wrap deleted | Access revoked | Re-invite creates new wrap |
