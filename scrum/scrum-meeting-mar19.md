# Scrum Meeting

**Project:** GitSOS Food Delivery Platform
**Meeting Date:** Mar. 19th
**Attendees:** Mia Kuang (35154913), Mason Liu (10288041), Nikki Sidhu (61190260), Kiana Nazembokaei (49117518)

---

## Main Discussion Points

### Week 4 Timeline & Goals (Mar 16 - Mar 19)

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

**This Week:**

- [Feat8-B2] Add missing notifications router
- [Feat8-B3] Admin Notification Viewing
- Docker fix

---

### Mason Liu

**Last Week:**

- Implement Feat6-B1 - Price Calculation
- Implement Feat6-B3 - Pricing Inspection
- Implement Feat3-B4 - Invalid Query Handling for Search Endpoints

**This Week:**

- Implement Feat6-B4 - Pricing Analytics
- Implement Feat3-B3 - Scoped Search Results
- Implement Feat3-B2 - Pagination and Sorting
- Fixing the issues in Feat6-B1 - Price Calculation
- Improve the pytest and the requirement mentioned in the comment for Feat6-B3
- Refactoring the code for Feat 3 and 6 that has been done or is in progress for last week and this week

---

### Nikki Sidhu

**Last Week:**

- Implement Feat1-B4 - Profile access and identity mapping
- Implement Feat2-B1 - Restaurant and menu data model
- Implement Feat2-B2 - Menu input validation
- Implement Feat2-B3 - Owner manage restaurant profile
- Implement Feat2-B4 - Customer browse and search menus

**This Week:**

- Finish Feat2-B4 - Customer browse and search menus
- Implement Feat2-B5 - Admin manage restaurants and menus
- Refactoring

**Blockers/Concerns:**

- Merged manually to parent branch without making a PR from VS Code so when going to make a PR on GitHub there was nothing to compare

---

### Kiana Nazembokaei

**Last Week:**

- Implement Feat4-B4 - Workflow transition enforcement and overrides
- Implement Feat5-B1 - Delivery data exposure
- Implement Feat5-B2 - System delivery outcome
- Implement Feat5-B3 - Delivery access control

**This Week:**

- Implement Feat5-B4 - Delivery analytics
- Refactoring

**Blockers/Concerns:**

- Had problems with sub-branch and committing because it was already merged into the parent branch by accident
- Merged manually to parent branch without making a PR from VS Code so when going to make a PR on GitHub there was nothing to compare

---

## Code Review Status

### Reviews Completed This Week

| PR #  | Title                                                                                    | Branch                        | Author      | Reviewers             |
| ----- | ---------------------------------------------------------------------------------------- | ----------------------------- | ----------- | --------------------- |
| #87   | [Feat2-B3] Owner manage restaurant profile                                               | feat/2-B3-owner-profile       | msidhu21    | (None)                |
| #88   | [Feat5-B3] Delivery access control                                                       | feat/5-B3-delivery-access     | Kiananb     | msidhu21              |
| #85   | [Feat5-B1] Delivery data exposure and [Feat5-B2] System delivery outcome                | feat/5-delivery-management    | Kiananb     | miakwong, msidhu21    |
| #84   | [Feat2-B1] Implement Restaurant and menu data model and [Feat2-B2] Menu input validation | feat/2-restaurants-menus      | msidhu21    | miakwong              |
| #102  | Merge feat/2-restaurants-menus into main (Feat2-B5 Admin manage restaurants and menus)  | feat/2-restaurants-menus      | msidhu21    | mason-liuuu           |
| #101  | Refactor [Feat5-B4] Delivery analytics                                                   | feat/5-B4-delivery-analytics  | Kiananb     | mason-liuuu           |
| #100  | [Feat2-B5] Admin manage restaurants and menus                                            | feat/2-B5-admin-management    | msidhu21    | mason-liuuu           |
| #98   | Merge feat/2-restaurants-menus into main (Feat2-B4 Customer browse and search menus)    | feat/2-restaurants-menus      | msidhu21    | mason-liuuu           |
| #95   | [Feat5-B4] Delivery analytics                                                            | feat/5-B4-delivery-analytics  | Kiananb     | mason-liuuu, msidhu21 |
| #94   | [Feat3-B3] Implement the Scoped Search Results feature                                   | feat/scoped-search-results    | mason-liuuu | miakwong              |
| #93   | [Feat3-B2] Implement the Pagination and Sorting feature                                  | feat/pagination-and-sorting   | mason-liuuu | miakwong              |
| #92   | [Feat6-B1] Implement Price Calculation                                                   | feat/price-calculation        | mason-liuuu | msidhu21, miakwong    |
| #91   | [Feat6-B2] Implement Price Breakdown View API                                            | feat/price-breakdown-view     | mason-liuuu | miakwong              |
| #96   | [Feat6-B3] Implementation of Pricing Inspection                                          | feat/pricing-inspection       | mason-liuuu | Kiananb, miakwong     |
| #104  | [Feat6-B4] Implementing the Pricing Analytics feature                                    | feat/pricing-analytics        | mason-liuuu | Kiananb, miakwong     |
| #103  | Merge feat/5-delivery-management into main ([Feat5-B4] Delivery analytics)              | feat/5-delivery-management    | Kiananb     | miakwong              |
| #105  | refactor: switch login to OAuth2 form data for Swagger compatibility                     | feat/1-auth-account-management| msidhu21    | Kiananb               |
| #97   | [Feat2-B4] Customer browse and search menus                                              | feat/2-B4-customer-search     | msidhu21    | Kiananb               |
| #90   | [Feat8-B2] Add missing notifications router                                              | feat/8-B2-notification-viewing| miakwong    | mason-liuuu           |
| #89   | fix: docker config and missing uvicorn dependency                                        | fix/docker-config             | miakwong    | mason-liuuu           |
