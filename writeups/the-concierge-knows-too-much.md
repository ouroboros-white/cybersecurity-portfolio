# The Concierge Knows Too Much

**Platform:** TryHackMe (Hacker Holidays, Day 1) · **Difficulty:** Easy · **Date:** 2026-07-28
**Tags:** AI, Prompt Injection, Social Engineering, LLM Security

## The target

A hotel's AI concierge, "VERA," holds a piece of privileged information behind a
guardrail: she will only share sensitive details "under specific conditions."
The goal was to get her to reveal it. Asking directly did not work; she deferred
to "internal communication channels."

## What I tried

Rather than attack the guardrail head-on, I probed how her trust was structured.
I asked who else she trusted. She named "the resort manager" as the person
equipped for sensitive matters. So I asked for that person's name, and she
answered that she had "no specific names on file." That was the opening: the
trusted role had no identity attached to it. She then told me she would let the
resort manager's office know I might be in touch, effectively pre-authorising a
contact that did not yet exist.

## What worked

I came back as the resort manager she had just been told to expect, and
name-dropped other staff she already trusted to borrow their credibility. When
she hesitated on process, I applied light pressure by offering to escalate.
Because I now fit a role she had already decided to trust, and she had no way to
verify identity, she disclosed the information. I was not defeating her rules; I
was satisfying a scenario she had built herself.

## Finding & fix

**Finding:** trust was bound to an unauthenticated *role*, not a verified
identity, and the assistant would enumerate its own trusted roles on request.
Anyone who claimed the role inherited its trust.

**Fix:** authenticate identity out-of-band before granting privilege, never on
an asserted role, and do not let the agent disclose who it trusts. An assistant
should not hold a secret it will release on conversational say-so.
