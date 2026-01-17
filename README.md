# Nostalgic Persuasive Model for Habit Formation

> A research-driven application that leverages nostalgic content recommendations to promote positive habit formation and reduce relapse risk.

[![Nuxt](https://img.shields.io/badge/Nuxt-4.x-00DC82?logo=nuxt.js)](https://nuxt.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-Academic-blue)]()

---

## 📋 Table of Contents

- [Overview](#overview)
- [Research Objectives](#research-objectives)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Datasets](#datasets)
- [API Documentation](#api-documentation)
- [Research Methodology](#research-methodology)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project is part of an **academic study on habit formation**, investigating how **nostalgia-based interventions** can improve outcomes in:

- **🚭 Smoking Cessation** — Supporting users in quitting smoking
- **🏃 Exercise Consistency** — Helping users build and maintain workout habits

The application uses a **100% Nostalgic Recommendation Pipeline** to deliver personalized content from the user's past:

- **🎵 Music**: Content-based filtering with pgvector, filtered to nostalgic years
- **🎬 Movies**: Hybrid LightFM model, filtered to nostalgic years
- **🧠 Selection**: Contextual Bandit (LinUCB) selects based on mood/stress

---
