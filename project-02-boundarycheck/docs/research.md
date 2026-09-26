# FDE role research and project rationale

**Reviewed: September 26, 2026.** I skimmed primary career pages for a sample of high-compensation FDE and forward-deployed security roles. Advertised base pay is not total compensation, may change, and varies by location and candidate. It is a snapshot, not a ranking of engineering quality.

## Postings reviewed

| Employer / role | Advertised base range | Repeated signals in the posting |
| --- | ---: | --- |
| [OpenAI · Forward Deployed Security Engineer](https://openai.com/careers/forward-deployed-security-engineer-washington-dc/) | $266K–$445K + equity | Embedded customer security delivery from design through production and operations; access control, authentication, encryption, network/system security; cloud, Kubernetes/Terraform; Python or Go; threat monitoring and cross-functional work |
| [Anyscale · Forward Deployed Engineer](https://jobs.ashbyhq.com/anyscale/52167dfd-c1b0-4e8a-b64c-b5710e176535/) | $266,970–$287,043 | Work with strategic customers; deployments and adoption; translate goals into measurable outcomes; Kubernetes and ML infrastructure; communicate with technical and executive stakeholders; feed learnings back into the product |
| [OpenAI · Forward Deployed Engineer, SF](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/) | $185K–$300K + equity | Own discovery, scope, system design, build, rollout, production adoption, measurable workflow impact, evaluations, and field feedback |
| [OpenAI · Forward Deployed Engineer, Healthcare](https://openai.com/careers/forward-deployed-engineer-%28fde%29-healthcare-sf-san-francisco/) | $185K–$300K + equity | Full delivery in a regulated customer environment; privacy, security, governance, evaluation criteria, human review, reliability, integrations, production handoff |
| [Palantir · Forward Deployed Software Engineer, Warp Speed](https://jobs.lever.co/palantir/13f99633-43b5-4459-8e84-25073f257c18) | Posting page did not expose a range in the reviewed content | Build software with customers; own outcomes in technically complex environments; communicate clearly across stakeholders |

The exact compensation numbers above are copied from the linked employer postings as reviewed on the date shown. A listing's availability and compensation can change; click through to confirm current details.

## Skill pattern

The shared pattern is broader than a particular framework:

1. **Discovery and scope:** turn a customer workflow with fuzzy edges into an agreed first release.
2. **Build and integration:** write practical production code that fits existing identity, data, and infrastructure.
3. **Safe operation:** consider least privilege, boundaries, telemetry, failure behavior, and handoff before launch.
4. **Evaluation and outcomes:** define measurable acceptance criteria and look at real workflow impact.
5. **Customer communication:** make trade-offs understandable to operators, engineers, and leadership.
6. **Learning loop:** capture field feedback as reusable patterns and product changes.

## How those signals shaped BoundaryCheck

BoundaryCheck focuses on a customer-specific launch profile rather than a generic AI chatbot. It has a written scope, an inspectable design, a runnable CLI, security-oriented test cases, a small measured evaluation, and a final handoff report. Findings include evidence and a fix so the tool demonstrates both technical depth and clear delivery communication. The project is deliberately local-first and deterministic; that is an implementation choice for a safe, repeatable portfolio demo, not a requirement stated by every employer.

## Sources

- [OpenAI Forward Deployed Security Engineer](https://openai.com/careers/forward-deployed-security-engineer-washington-dc/) — compensation and security/cloud/customer lifecycle requirements.
- [Anyscale Forward Deployed Engineer](https://jobs.ashbyhq.com/anyscale/52167dfd-c1b0-4e8a-b64c-b5710e176535/) — compensation, customer outcomes, enterprise adoption, ML/Kubernetes, stakeholder communication.
- [OpenAI Forward Deployed Engineer (SF)](https://openai.com/careers/forward-deployed-engineer-%28fde%29-sf-san-francisco/) — end-to-end deployment ownership, evals, adoption, and feedback.
- [OpenAI Forward Deployed Engineer, Healthcare](https://openai.com/careers/forward-deployed-engineer-%28fde%29-healthcare-sf-san-francisco/) — regulated delivery, privacy, governance, human review, and launch criteria.
- [Palantir Forward Deployed Software Engineer, Warp Speed](https://jobs.lever.co/palantir/13f99633-43b5-4459-8e84-25073f257c18) — customer-facing software delivery context.
