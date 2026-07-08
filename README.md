# swell-demo

A demo repo for swell, an AI software engineering coach that helps you practice data structures and algorithms through realistic technical interviews.

## Task 1: Defining Problem, Audience, and Scope

Software engineers struggle to prepare effectively for technical interviews because practicing coding problems alone does not replicate the experience of a real interview.

Software engineers preparing for technical interviews need to develop both strong data structures and algorithms skills and the ability to solve problems under interview conditions. Their goal is not only to arrive at the correct solution, but also to communicate their thought process, respond to hints, justify trade-offs, and collaborate effectively with an interviewer.

Today, most candidates prepare by solving problems on platforms like LeetCode or HackerRank, watching solution videos, or practicing occasionally with friends through mock interviews. While these approaches help build algorithmic knowledge, they provide little opportunity to practice the interactive aspects of a real interview, such as verbalizing reasoning, receiving incremental feedback, handling interviewer prompts, or adapting to changing requirements. As a result, many candidates enter interviews technically prepared but lacking confidence and experience in the collaborative problem-solving process that interviewers actually evaluate.

```mermaid
flowchart TD
    A[Decide to prepare for technical interviews]
    B[Find DSA problems<br/>LeetCode, HackerRank, etc.]
    C[Solve problems independently<br/>in an IDE]
    D[Review editorials,<br/>discussion forums,<br/>or YouTube videos]
    E[Practice explaining solution<br/>alone or skip entirely]
    F[Occasionally schedule<br/>a mock interview<br/>with a friend or interviewer]
    G[Attend a real<br/>technical interview]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G

    P1{{Finding relevant<br/>questions is time-consuming}}
    P2{{Limited feedback<br/>on reasoning}}
    P3{{Static solutions don't adapt<br/>to the learner}}
    P4{{Communication skills<br/>rarely practiced}}
    P5{{Scheduling mock interviews<br/>is difficult}}

    B -.-> P1
    C -.-> P2
    D -.-> P3
    E -.-> P4
    F -.-> P5

    classDef pain fill:#ffe5e5,stroke:#d9534f,color:#a94442;
    class P1,P2,P3,P4,P5 pain;
```

Questions to evaluate the application:
- Does the AI avoid giving away the solution immediately?
- Does the AI ask follow-up questions after the user proposes an approach?
- Does the AI encourage the user to explain their reasoning before coding?
- Does the AI generate actionable feedback after the interview?
