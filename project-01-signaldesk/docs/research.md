# FDE role research and project fit

## Scope and method

This is a skim of public U.S. job postings available on **September 25, 2026**. Compensation figures below are advertised base salary ranges unless a source says otherwise. The range is not a promise of an offer or total compensation. High-paying postings vary by location, level, equity, and what each employer labels “salary.”

## A sample of roles

| Employer / role | Posted compensation | What the posting emphasizes | Source |
| --- | ---: | --- | --- |
| OpenAI — Forward Deployed Engineer, U.S. roles | $185K–$300K shown on the current FDE job board listing; equity and bonus may add to total compensation | Partner with customers to bring frontier model work into production; applied engineering and deployment | [OpenAI FDE posting](https://jobs.ashbyhq.com/openai/dc17edac-2993-4318-812a-14864c6f4658) · [FDE Jobs listing](https://www.fdejobs.com/jobs) |
| Anyscale — Forward Deployed Engineer, San Francisco | $266,970–$287,043 | Work with strategic customers; scale applications with Ray; Spanish for some Latin America customers | [Anyscale posting](https://jobs.ashbyhq.com/anyscale/52167dfd-c1b0-4e8a-b64c-b5710e176535/) |
| Palantir — Forward Deployed Software Engineer, Warp Speed, New York | $135K–$200K | Work from factory floor to board room; customer data, AI, custom applications, large-scale data, architecture, end-to-end deployment; Python/Java/C++/TypeScript | [Palantir posting](https://jobs.lever.co/palantir/13f99633-43b5-4459-8e84-25073f257c18) |
| Profound — Forward Deployed Engineer, NYC/SF | $140K–$260K base | Production-quality delivery for enterprise customers, customer communication, explain technical ideas, cross-functional ownership, and business outcomes | [Profound posting](https://jobs.ashbyhq.com/Profound/b076c997-0ba3-4d3c-9dc9-ad0b3ed49b05?employmentType=FullTime) |
| Growth Protocol — Forward Deployed Engineer, U.S. | $150K–$180K base, plus equity/bonus | Deploy AI/ML workflows; Python, cloud, Docker, APIs, data pipelines/distributed systems; technical design and executive communication | [Growth Protocol posting](https://jobs.ashbyhq.com/growthprotocol/bdb23236-dbb5-48a4-8f5c-3325fd03c8ee) |
| P-1 AI — Forward Deployed Engineer, U.S. remote | $160K–$200K, plus equity | Industrial customer implementation and engineering tool use | [P-1 AI posting](https://jobs.ashbyhq.com/P-1%20AI/0be87478-22fd-4a03-b1d2-553347f87cf1/) |

**Salary context:** current FDE Jobs aggregation reports that disclosed postings average about $184K–$250K and lists OpenAI role compensation estimates as high as $280K–$550K total compensation, with a caveat that it blends postings, public compensation disclosures, and levels data. This is a secondary aggregation, not a direct employer offer range: [FDE Jobs salary guide](https://www.fdejobs.com/salaries). Treat total compensation separately from advertised base.

## Repeated skill signals

1. **Own the full delivery loop:** turn a customer problem into a scoped design, working software, deployment, iteration, and a measurable outcome.
2. **Code across the stack:** Python appears repeatedly; postings also name TypeScript/JavaScript, Java, or C++. Engineers need to work with APIs, data structures, and user-facing tools.
3. **Integrate messy customer data:** normalize records from catalogs, feeds, databases, and existing systems; validate assumptions and handle incomplete inputs.
4. **Use applied AI responsibly:** make AI/ML useful in an operational workflow, evaluate the result, and know when to surface uncertainty or ask for human review.
5. **Operate in production-shaped environments:** cloud infrastructure, Docker, data pipelines, distributed systems, reliability, and integration boundaries.
6. **Work directly with stakeholders:** communicate with engineers and executives, explain tradeoffs simply, and keep scope aligned as requirements evolve.
7. **Connect engineering to business impact:** identify costly friction, choose measurable success criteria, and produce repeatable solutions rather than one-off demos.

## How SignalDesk demonstrates the pattern

SignalDesk turns this synthesis into a narrow and runnable case study. It takes multiple data shapes, maps an incident to its service owner, retrieves source-linked runbooks, surfaces recent changes, and exposes a responsive operator view and JSON API. Golden scenarios and test cases measure the behavior. A human-review gate and explicit scope limitations show that production deployment includes access and safety decisions, not only a clever model.

The prototype does not claim that a tiny keyword baseline is a cutting-edge AI system. Its value is showing a complete customer-facing engineering process with clear evidence and a path for deeper validation.

