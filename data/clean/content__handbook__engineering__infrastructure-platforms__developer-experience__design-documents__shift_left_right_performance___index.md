## Summary

Performance is a critical aspect of software quality that directly impacts user satisfaction and business success. We recognize that performance testing is not just a final step in development but an integral part of our entire software lifecycle. This blueprint outlines our comprehensive approach to performance testing, which goes beyond traditional load testing to encompass a wide range of techniques and practices.

We believe in shifting performance testing both left (early in development) and right (into production monitoring) to create a culture of continuous performance awareness. By integrating performance considerations at every stage - from unit testing to production monitoring - we aim to identify and address performance issues early, optimize our systems proactively, and deliver a consistently high-performing product to our users.

This guide serves as a resource, showcasing our strategies, tools, and best practices for performance engineering. It demonstrates our commitment to excellence and our innovative approach to ensuring that GitLab remains fast, responsive, and scalable as we continue to grow and evolve.

## Motivation

We have been successfully using tools like [GPT](https://gitlab.com/gitlab-org/quality/performance) for load testing against [Reference Architectures](https://docs.gitlab.com/ee/administration/reference_architectures/). We have had experiences, such as [database performance testing with large datasets](https://gitlab.com/gitlab-org/gitlab/-/issues/434465), that have demonstrated the benefits of shifting performance testing left in the development process.

By adopting a broader range of performance engineering practices, we can take a more proactive stance on solving performance concerns before they surface as issues in live environments. This approach aligns with our commitment to delivering excellent user experiences and maintaining GitLab's scalability as we continue to grow.

### Goals

* More complete documentation on Performance Engineering practices in [the handbook page](/handbook/engineering/testing/performance-tools/)
* Develop a plan for adopting these practices across all Engineering teams.
* Create a culture of performance awareness throughout the entire software development lifecycle.
* Improve early detection and resolution of performance issues.
* Enhance GitLab's overall performance and scalability.
* Standardize prioritization of performance issues at GitLab, so it no longer varies team to team with the lowest possible standard being “in response to production incident”.
* Ingrain performance earlier into the development process

### Non-Goals

* Performance becomes something that another team is responsible for owning and driving (the individual teams should have ownership of their own performance goals)
* Performance is seen as a checklist / gatekeeper item that has to be done to progress

## Proposal

Our proposed Shift Left and Right Performance Testing Strategy includes:

1. Shift Left approaches:
   * Unit Testing: Implement performance-focused unit tests using tools like benchmark-ips for Ruby.
   * Early Profiling: Integrate profiling tools like ruby-prof into the development pipeline.
   * Continuous Performance Awareness: Use instrumented tests and observability tools throughout development.

2. Shift Right approaches:
   * Load Testing: Continue and enhance our use of GitLab Performance Tool (GPT) for load testing.
   * Production Monitoring: Implement real-time observability and user-centric performance metrics in production.
   * Chaos Engineering: Introduce controlled failures to test system resilience.

3. Tool and technique adoption:
   * Drive adoption of modules for unit-level performance testing
   * Integrate profiling tools into the development pipeline
   * Implement observability tools for ongoing performance monitoring

4. Training and culture:
   * Develop training programs for engineers on performance testing techniques
   * Establish performance benchmarks and goals for each development stage
   * Create a system for sharing performance insights across teams

## Design and implementation details

## Alternative Solutions

1. Maintain current GPT-focused approach:
   * Pros: Familiar process, less initial effort
   * Cons: Misses opportunities for early performance optimization, may lead to costly late-stage fixes

2. Focus solely on production monitoring:
   * Pros: Real-world data, less impact on development process
   * Cons: Reactive rather than proactive, potential for user-impacting issues

3. Implement full shift-left without shift-right:
   * Pros: Early issue detection, potentially faster development
   * Cons: May miss real-world performance issues, less comprehensive approach

The proposed Shift Left and Right strategy provides a balanced and comprehensive approach to performance testing, addressing the limitations of these alternatives.
