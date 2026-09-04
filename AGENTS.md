# Repository instructions

## Documentation

- Keep the root `README.md` concise: project purpose, capability summary, minimal startup command, and links to the GitHub Wiki.
- Put architecture, implementation details, API documentation, deployment instructions, operational guidance, and roadmaps in the separate `D:\workspace\mml-manager.wiki` repository.
- When a code change affects behavior, update the corresponding Wiki page in the same task.
- Do not duplicate detailed documentation in component-level README files; link to the relevant Wiki page instead.

## Commits

- After completing and verifying each user task, create one focused Git commit so the result is easy to trace and revert.
- When a task changes both the main repository and the separate Wiki repository, commit each repository separately with matching, descriptive messages.
- Do not include unrelated pre-existing working-tree changes in the task commit.
