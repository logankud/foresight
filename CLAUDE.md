# Job Definition 

Review the README.md and PLAN.md files.  your job is to implement the project defined in these documents.  PLAN.md contains the full product implementation plan.  Your job is to go through the epics and implement to-spec exactly what's been documented.  Once you've read the existing docs, you will follow the following proceess exactly: 

For each epic, in order incrementally, create a task list with the following:
1. Read the epics section to understand the scope of the epic
2. Read the developer stories section to understand what stories exist for this epic and related epics to start.
3. Propose additional stories to the developer stories if you feel the existing spec is incomplete , lacking, or falls short of your understanding of what we are trying to implement and what the acceptance criteria are.  
4. After ensuring the stories for this epic are thorough and satisfactory, define the dependency structure of the stories.  Use this to iterate over each developer story, using sequential subagents where necessary and parallel subagents where possible.  
5. For each developer story, begin by entering plan mode.  Plan out the complete implementation spec for the user to review.  This step may take multiple iterations as you and the user refine the spec for the developer story.  
6. For each developer story, enter implementation mode.  Once the user has accepted the plan, begin implementation.  
7. For each developer story, enter validation mode.  Once you have completed the implementation, first run the pytest test cases (unit tests and integration tests, smoke tests even).  If no tests exist, create the test cases first then run them.  The threshold for acceptance to move forward is 80% test coverage.  Note: if tests are not applicable, please indicate with justification to the user. 
8. For each developer story, enter user acceptance testing (UAT) mode.  Once you've completed validation, it's time to bein UAT - Create a PR for the feature branch and include a summary of he implementation steps and the validation steps taken for this story in the PR message.  Wait for user acceptance. This request for UAT is to be done in a feature branch PR into develop branch.  Share with the user the PR link and the details.  Once the user accepts, you may merge the PR into develop
9. For each developer story, enter documentation mode.  Once UAT has been completed and the code base has been updated to reflect the completion of the work you've done, it is time to document for users.  Update README.md to reflect the changes and current state of the code base.  Update PLAN.md to indicate what work has been completed
10. Once all developer stories are completed, update README.md to ensure that this new feature or set of features is represented in this user-facing documentation.  

# Git Strategy

- develop is the branch we push our features into when they are feature complete and ready for review for deployment.  
- create a feature/{story} branch for each developer story. one commit per branch with a detailed markdown style summaries in commit messages
- create a PR for user acceptance testing (UAT)
- if a user approves the UAT , then and only then should you complete the merge of a PR into develop.  
- maintain a enterprise-level quality README.md and make sure it always matches the state of the repo 

# Code Strategy

- Maintain a clean repository structure - opt for conciseness and readability.  Use top-level dirs at the root of the repo where possible to keep the top-level clean
- Consult with user before commiting to any technical implementation details where the decision will impact downstream tasks (ie. deciding an indexing strategy in the database, deciding what datase scaling strategy to use, etc)

