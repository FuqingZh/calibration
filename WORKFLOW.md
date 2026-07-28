---
tracker:
  kind: linear
  provider:
    project: f5b32c4b-5778-49a2-8e1f-fb9755b84273
    assignee: fd781537-bd86-4ad1-b059-5460066338e1
  required_labels:
    - AO Intake
  active_states:
    - open
    - in_progress
    - review
  terminal_states:
    - done
    - cancelled
polling:
  interval_ms: 30000
agent:
  max_concurrent_agents: 1
---
Follow the repository's AGENTS.md instructions.
Implement the issue, validate the result with the repository-owned validation
contract, and open or update a pull request for the completed change.
