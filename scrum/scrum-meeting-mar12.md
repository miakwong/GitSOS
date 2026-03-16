# Scrum Meeting

**Project:** GitSOS Food Delivery Platform
**Meeting Date:** Mar. 12th
**Attendees:** Mia Kuang (35154913), Nikki Sidhu (61190260), Kiana Nazembokaei (49117518)

---

## Main Discussion Points

### Week 3 Timeline & Goals (Mar 12 - Mar 17)

- **Primary Focus:** All core feature implementation
- **Week Objective:** Each team member completes all features and test endpoints
- **Target Deliverables:**
  - Multiple PRs submitted by the end of the week
  - Service layer business logic finish
  - API endpoints for assigned features
  - Comprehensive test coverage (>85% target)

---

## Individual Assigned Action

### Mia Kuang

**Last Week:**
- Feat7-B2 - Payment Status View
- Feat7-B3 - Payment Access Control
- Testing & Documentation

**This Week:**
- Feat8
- Solve conflicts and start essential refactor

---

### Nikki Sidhu

**Last Week:**
- Implement Feat1-B1 - Auth Registration and Login
- Implement Feat1-B2 - Token Lifecycle and Logout
- Structure and organize backend documentation
- Implement the initial FastAPI backend setup, including creating the main application entry point and verifying that the API runs correctly

**This Week:**
- Implement Feat1-B3 - Role-Based Access Control
- Implement Feat1-B4 - Profile access and identity mapping
- Implement Feat2-B1 - Restaurant and menu data model
- Implement the initial FastAPI backend setup, including creating the main application entry point and verifying that the API runs correctly

**Blockers/Concerns:** [Any issues or concerns]

---

### Kiana Nazembokaei

**Last Week:**
- Implement Feat4-B3 - Owner order views
- Implement Feat4-B4 - Workflow transition enforcement and overrides
- Implement Feat5-B1 - Delivery data exposure

**This Week:**
- Implement Feat4-B3 - Owner order views
- Implement Feat4-B4 - Workflow transition enforcement and overrides
- Implement Feat5-B1 - Delivery data exposure

**Blockers/Concerns:** [Any issues or concerns]

---

## Code Review Status

### Reviews Completed This Week

| PR# | Title | Branch | Author | Reviewers |
|-----|-------|--------|--------|-----------|
| #74 | Merge feat/1-auth-account-management (Feat1-B3 RBAC) | feat/1-auth-account-management | msidhu21 | Kiananb |
| #73 | [Feat4-B3] Owner order Views | feat/4-B3-owner-views | Kiananb | — |
| #72 | [Feat1-B3] Implement Role-Based Access Control | feat/1-B3-role-control | msidhu21 | — |
| #71 | Merge Feat/4-order-workflow (Feat/4-B2-customer-rules) | feat/4-order-workflow | Kiananb | miakwong |
| #70 | feat: payment access control (Feat7-B3) | feat/7/access-control | miakwong | Kiananb (×3) |
| #69 | Merge feat/1-auth-account-management (Token lifecycle) | feat/1-auth-account-management | msidhu21 | Kiananb |
| #68 | [Feat3-B1] Search Filters (Restaurants, Menu, Orders) | feat/search-filter | mason-liuuu | msidhu21 |
| #67 | [Feat1-B2] Token lifecycle and logout handling | feat/1-B2-token-lifecycle-logout | msidhu21 | — |
| #66 | [Feat7-B2] Payment status view endpoints | feat/7/status-view | miakwong | msidhu21 (×2) |
| #65 | [Feat4-B2] Order modification and cancellation | feat/4-B2-customer-rules | Kiananb | msidhu21 |
| #64 | feat(payment): payment service core — process & lookup | feat/7/payment-core | miakwong | msidhu21 (×2) |
| #63 | Merge feat/1-auth-account-management into main | feat/1-auth-account-management | msidhu21 | miakwong, msidhu21 |
| #62 | Merge feat/4-order-workflow into main | feat/4-order-workflow | Kiananb | miakwong (×3) |
| #61 | [Feat1-B1] User registration and login with JWT | feat/1-B1-auth-registration-login | msidhu21 | Kiananb |
| #59 | feat/payment-repository: JSON persistence layer | feat/payment-repository | miakwong | Kiananb |
| #58 | feat/kaggle-data-layer: Restaurant, Menu & Order Data | feat/kaggle-data-layer | miakwong | mason-liuuu, msidhu21 |
| #56 | [Feat4-B1] System order creation with validation | feat/4-B1-system-order | Kiananb | miakwong (×2) |
| #54 | Feat/7 schemas and constants | feat/7/schemas-and-constants | miakwong | — |
