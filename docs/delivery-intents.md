# Delivery Intents

Domain strategy, deployment architecture, and content delivery documentation.

---

## Purpose

This section documents the **intent and strategy** for content delivery across domains, CDN, social media, and other channels.

**Note:** Infrastructure implementation details (CI/CD, deployment scripts) belong in application repositories. This directory captures the **strategic decisions** that inform infrastructure.

---

## Domain Strategy

**[Domain Strategy Document](domain-strategy.md)** - Complete content-to-domain mapping baseline

Key topics covered:
- Brand hierarchy and business model
- Three information flow dimensions (Solutions, Regional, Enterprise)
- Domain architecture (Tier 1, 2A, 2B, 3)
- URL structure and subdomain conventions
- Implementation guidance

---

## Planned Documentation

- **cdn-architecture.md** - Edge delivery patterns and caching strategies
- **social-media-matrix.md** - Platform-specific content adaptation strategies
- **deployment-checklist.md** - Pre-launch verification and go-live procedures

---

## Domain Architecture Overview

### Tier Structure
- **Tier 1:** Corporate hub (omnivoltaic.com)
- **Tier 2A:** Solutions (use-case driven)
- **Tier 2B:** Regional operations (OVK, OVT, etc.)
- **Tier 3:** Platform capabilities (docs, assets, enterprise)

See [domain-strategy.md](domain-strategy.md) for complete architecture.
