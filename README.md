# Customer Projects

This repository contains several customer-focused web applications created with Claude Code sub-agents and specification-driven development.

Each project is a Python application built with Flask, SQLAlchemy, Alembic, and related tools to expose REST APIs for CRUD operations on a PostgreSQL database. All projects run in Docker containers for both the application server and the database.

# Objective

The main goal is to use Claude Code and structured specifications to build software and compare different development approaches using sub-agents, technical requirements, and functional requirements.

## Customer Hybrid

This project was created in two phases.

- The first phase covers the customer API and CRUD operations and was built without a sub-agent.
- A Claude Code sub-agent was then created using the first phase as a reference to learn the architecture, coding style, and overall project characteristics.
- The second phase adds the address API and CRUD operations and was implemented by a Claude Code sub-agent using the technical specification.

## Customer SDD

This project was developed entirely by a Claude Code sub-agent using both technical and functional specifications.

The sub-agent acts as a software engineer with knowledge of hexagonal architecture, SOLID principles, object-oriented programming, microservices, and APIs. The technical stack includes Python, Flask, SQLAlchemy, and PostgreSQL.

## Customer Subagent

This project was also developed by a Claude Code sub-agent, with a technical specification as the main reference.

The sub-agent acts as a backend engineer with knowledge of hexagonal architecture, SOLID principles, object-oriented programming, microservices, and APIs. It is also language-agnostic and adaptable to different technologies. The technical specification defines the project contracts and the chosen stack: Python, Flask, SQLAlchemy, and PostgreSQL.

# Conclusions

This approach works well for building small to medium-sized backend services with a clear structure and consistent patterns.

Creating a Claude Code sub-agent that is language-agnostic and adaptable to different technologies helps reuse the same workflow in other projects.

Using functional specifications with business requirements and rules produces more accurate results and reduces misunderstandings during implementation.

Using technical specifications to define contracts, architecture, and stack choices also improves consistency and reduces ambiguity across the project.