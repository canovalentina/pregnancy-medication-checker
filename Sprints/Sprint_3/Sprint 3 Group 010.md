# Final Project Sprint 3: CS 6440

## Lana P kareem, Valentina Cano Arcay, Faezeh Goli [lkareem6@gatech.edu](mailto:lkareem6@gatech.edu), [varcay3@gatech.edu](mailto:varcay3@gatech.edu), [faezeh@gatech.edu](mailto:faezeh@gatech.edu)

# **1 ACCOMPLISHEMENTS**

By the previous Sprint (Sprint 2\) due date, the scope of our project was finalized with our mentor, and the sprint was delivered by the deadline. The submission included details about our technical design, required APIs and data sources, architecture diagram, screen mock-ups, and implementation plan with assigned tasks and timelines. We also developed a detailed project timeline outlining each step and elaborated on potential risks that might arise during the project.

Since the last project check-in, each team member has been assigned specific tasks to complete over the past two weeks, from October 13 to the Sprint 3 deadline on October 27\. 

Below is a detailed list of the tasks completed by each group member, along with the estimated number of hours each member spent per week since the last check-in.

## **1.1 Faezeh**

My plan for two weeks, ending by the Sprint 3 deadline, is to verify availability and documentation for all the APIs and data sources we will need for our group project.  
I will also create connection examples and add code snippets to my reports, before sharing them with my teammates.   
Any identified challenges in integration and also the solution I might suggest, will also be attached.  
For the first week, I want to make sure we fully understand documentation and check access requirements and endpoints for each API. It is also crucial to know the syntaxes for connections and what data each data source would provide.  
The breakdown of my work for week 1 and 2, leading to Sprint 3 deadline is as follows:

Week 1:

* Fast API \[1\] and PubMed \[2\] (2 hours)  
  * Reviewing the Fast API documentation  
  * Searching the PubMed API  
* RxNorm API \[3\] (2 hours)  
  * Reviewing RxNorm documentation  
  * Note on required endpoints to support autocomplete and normalization  
* OpenFDA API \[4\] (2 hours)  
  * Reviewing OpenFDA drug event API documentation  
  * Note on parameters, and filtering   
* FHIR API \[5\] (2 hours)  
  * Reviewing FHIR R4 resources.  
    * Observation, Condition, MedicationRequest  
  * Understand JSON response structure.  
* Summarizing the notes (1 hour)  
* Creating a short document (1 hour)  
  * Creating a document including the summary of notes taken, from reviewing documentations, including the API’s base URL, endpoints, and response format.  
  * Identifying the missing connections between APIs.

Week 2:

* OMOP CDM \[6\] (2 hours)  
  * Reviewing OMOP documentation  
  * Mapping OMOP columns to FHIR  
* DrugBank integration \[7\] (2 hours)  
  * Exploring DrugBank API  
  * Identify if DrugBank open data, covers interaction  
* SQLAlchemy \[8\] (1 hour)  
  * Exploring a small model and investigate how to create dummy data  
* Listing challenges we might face during our implementation (1 hour)  
* Exploring the next required steps for UI design (1 hour)  
* Adding second week notes to the report (1 hour)  
* Preparing the Sprint 3 draft and share with the team (1 hour)  
* Adding my tasks breakdown to the Sprint draft (1 hour)

## **1.2 Lana**

My goal for this sprint was to establish the backend environment and create the initial project skeleton. In week 1 of 2 of this sprint, I made the following progress: 

* Structured the repository with separate frontend and backend directories.   
* Setup the backend:  
  * Created the app/[main.py](http://main.py) (where the core functionality will be located) with root, /api/health, and /api/version endpoints.   
  * Added CORS middleware to allow future frontend requests from [http://localhost:5173](http://localhost:5173).   
  * Defined environment variables in the .env file, with variables such as APP\_NAME, API\_PREFIX, etc.   
  * Setup the dependencies for the backend in requirements.txt  
* Locally tested the backend  
  * When running FastAPI backend and navigating to [http://localhost:8000/docs](http://localhost:8000/docs) in my browser, FastAPI automatically provides an interactive page to monitor API endpoints (called Swagger UI)  
    * This page lists all the API endpoints (such as /api/health)  
    * Tests endpoints in the browser without needing curl or Postman  
    * Once more routes are added, they will automatically show on this page  
  * Confirmed that /api/health endpoint returns STATUS OK.  
  * Swagger docs located at /docs for future API development.

![][image1]

***Figure 1—***Confirmation of /api/health endpoint returning proper response.

* Setup Docker for containerization  
  * Created a first draft of Dockerfile.backend, Dockerfile.frontend, and docker-compose.yml. 

For week 1, here is how my time was divided for the above completed tasks: 

* 3 hours: environment setup (venv, dependencies, gitignore, repo structure).   
* 4 hours: writing and testing the main FastAPI app ([main.py](http://main.py)).   
* 3 hours: Drafting Docker files for backend and frontend. 

In week 2 of this sprint, my goal was to start setting up the frontend and try to connect it to the backend to have a blank UI to start with. Here is the progress I made with that: 

* Frontend setup attempt with Vite (React \+ TS)  
  * Command to set up the frontend (npm create vite@latest frontend \-- \--template react-ts) kept failing due to npm ETIMEDOUT errors when reaching the registry.   
  * I investigated the above issue further by checking npm registry access with curl and was able to verify that no proxy was set, however npm still times out.   
  * My next step to resolve this is turning off my VPN and trying to connect to a more stable internet.   
* Frontend src code setup  
  * The main files needed to set up the UI are prepared (main.tsx, App.tsx, index.html, package.json, tsconfig.json, vite.config.ts), but connection to the backend (/api/health endpoint) has not been verified yet in the browser. 

The following is the time breakdown in week 2: 

* 2 hours: npm/Vite troubleshooting (timeouts, proxies)  
* 5 hours: preparing React frontend main files (main.tsx, App.tsx)  
* 2 hours: setting up frontend dependencies (index.html, package.json, tsconfig.json, vite.config.ts)  
* 1 hour: searching possible frontend alternatives (Next.js)

## **1.3 Valentina**

My goal for these 2 weeks was to set up an initial connection to the FHIR server and ingest/search with some mock data.

Week 1 (6 hours)

* FHIR Client Library Research (2 hours): Investigated FHIR client libraries and FHIR R4 specifications to understand the API structure and best practices for server communication. Chose the [https://github.com/smart-on-fhir/client-py](https://github.com/smart-on-fhir/client-py) in Python since I have more experience in this language  
* Data Model Investigation (1.5 hours): Explored fhir.resources vs fhirclient.models libraries and identified where Pydantic models would be useful for API output validation  
* Project and Architecture Setup (2.5 hours): Created Makefile for task automation, pyproject.toml with uv dependency management for Python, and created a fhir\_integration folder within the backend part with interfaces/services/api separation (decided on this architecture for cleaner code, instead of having just one level for all classes). Created a README with some instructions on how to use the different make commands, so we can have consistency in development environments and standard formatting using lint and format. Refreshed my knowledge on Docker and added to the backend Dockerfile

Week 2 (13 hours)

* FHIR Service Implementation (4 hours): Built FHIRClient class with connection testing, patient search, and resource creation methods. Implemented error handling using Loguru for structured logging, added Python type hints. Created Pydantic data models and constants/enums to use throughout for better type-checking, error minimization, and cleaner code.  
* Data Ingestion System (3 hours): Created DataIngestion class with 5 realistic pregnancy-focused test patients, common pregnancy medications, pregnancy-related conditions, and pregnancy observations. Used JSON test data files for easy data management  
* API Integration (2 hours): Integrated FHIR services with FastAPI endpoints using clean handler pattern, creating various FHIR-related API endpoints in main.py  
* Testing and Debugging (3 hours): Created initial testing infrastructure, added test commands to Makefile, handled server data quality issues from public FHIR by adding fallback search mechanisms using direct HTTP requests when fhirclient validation fails, and fixed all error that came up after running make format and lint checks  
* Sprint Document (1 hour): Went over the tasks of these 2 weeks and completed my portion of this document, which was set up by Faezeh

# **2 CHALLENGES**

Below are the challenges each member of our group faced, or anticipated they might face, during their work and preparation for Sprint 3, organized by individual team members.

## **2.1 Faezeh**

I categorized the challenges I identified during my tasks by week.

Week 1 challenges:

* Exploring FastAPI, I found e parameters quite challenging to understand and manage.  
* RXNorm responses are complicated nested JSON.  
* There is a query limit, of 100 records max per page in OpenFDA Drug API, for interpreting adverse events, which is important to note.

Week 2 challenges:

* Mapping OMOP columns to FHIR resources, large datasets add complexity.  
* Licensing is required for full access to DrugBank API.  
* In completing my reports for my task, I found that in large documents, keeping notes concise and clear while summarizing them is quite a challenge. I try to maximize readability and keep the content short and to the point at the same time.

## **2.2 Lana**

The challenges I faced were mainly in week 2 with setting up the frontend, where I experienced time out errors when trying to run npm install. Creating the React app with Vite kept failing due to connectivity issues, and despite my debugging, I was not able to resolve this issue within the second week. My next attempt will involve turning off my VPN, as I found that this could be a potential blocker. This will likely reset the template code that I have created in the frontend folder in the repository, so in the upcoming sprint I will need to recreate the files within that folder. I plan to spend more time learning the details of Vite \+ [React.js](http://React.js) to ensure I can implement the frontend correctly once the repository setup is stable.  

In week 1, I did not face any blockers, but rather did but put in a good amount of effort in configuring the CORS correctly so that the frontend would be allowed to make requests later. 

## **2.3 Valentina**

* FHIR resources: When testing I had conflicts between fhir.resources and fhirclient.models libraries. I tried to use fhir.resources because it has comprehensive FHIR R4 models with built-in validation, but since fhirclient.models is specifically designed for SMART on FHIR server, I realized it was a better fit for server operations. I then decided to also create some custom Pydantic models for API output validation  
* Task Automation Tool Conflicts: Tried to use Taskfile (which I use professionally) but had conflicts with Taskwarrior both using the task command. After trying to resolve conflicts with aliases, I switched to Makefile which is simpler, more universally available, and avoids tool conflicts for better team collaboration  
* Public FHIR Server Data Quality Issues: the HAPI FHIR server had malformed data errors ("Narrative objects missing div properties") and Firely rejected the patient data with 400 Bad Request errors. In the end I kept HAPI but since search operations frequently failed, I had to implement a fallback to direct HTTP requests. For next sprint, I need to investigate these issues further and explore generating better synthetic data.

# **3 SPRINT PLANS**

## **3.1 Plans for the next 2 weeks**

The group’s plan for the next two weeks, until the next project check-in due date on November 10, is to implement the core interaction checker logic. This includes developing the frontend, connecting to the RxNorm API, and testing the overall functionality. On a more granular level, the team will implement the medication input form (frontend) and the backend endpoint to process the medication list, which involves connecting to the RxNorm API for medication normalization and autocomplete suggestions. The interaction checker logic will also be implemented using dummy data. Additionally, the team plans to integrate the required APIs, such as DrugBank for drug interaction data and PubMed for real-time research searches. We will continue to implement the FHIR API for patient data retrieval, which will be enhanced with better error handling and data validation, along with research into Synthea synthetic data generation to replace hard-coded test data with realistic and useful patient datasets. We will also implement the search functions for medications, observations, and conditions in the FHIR server.

# **4 REFERENCES**

1. Tiangolo. (n.d.). *FastAPI documentation*. Retrieved October 22, 2025, from   
   https://fastapi.tiangolo.com/  
2. National Center for Biotechnology Information. (n.d.). *PubMed help*. Retrieved October 22, 2025, from   
   https://pubmed.ncbi.nlm.nih.gov/help/  
3. National Library of Medicine. (2025, January 7). *RxNorm overview*. U.S. National Library of Medicine.  
   https://www.nlm.nih.gov/research/umls/rxnorm/overview.html  
4. U.S. Food & Drug Administration. (n.d.). *How to use the endpoint – Drugs@FDA (openFDA API)*. Retrieved October 22, 2025, from   
   [https://open.fda.gov/apis/drug/drugsfda/how-to-use-the-endpoint/](https://open.fda.gov/apis/drug/drugsfda/how-to-use-the-endpoint/)  
5. Health Level Seven International. (n.d.). *FHIR RESTful API (FHIR® specification)*. Retrieved October 22, 2025,  
   [https://build.fhir.org/http.html](https://build.fhir.org/http.html)  
6. Observational Health Data Sciences and Informatics. (n.d.). *OMOP Common Data Model (CDM)*. Retrieved October 22, 2025, from  
   [https://ohdsi.github.io/CommonDataModel/](https://ohdsi.github.io/CommonDataModel/)  
7. DrugBank Online. (n.d.). *About DrugBank Online*. Retrieved October 22, 2025, from  
   [https://go.drugbank.com/about](https://go.drugbank.com/about)  
8. SQLAlchemy authors. (n.d.). *SQLAlchemy: The Python SQL toolkit and object–relational mapper*. Retrieved October 22, 2025, from  
   [https://www.sqlalchemy.org/](https://www.sqlalchemy.org/)

[image1]: <data:image/png;base64,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>