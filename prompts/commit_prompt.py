from models.commit_request import CommitGenerationRequest


JSON_SCHEMA_EXAMPLE = """
{
  "recommended_commit": "fix(auth): resolve login form validation error",
  "alternatives": [
    "fix(login): correct form validation behavior",
    "refactor(auth): improve login form validation handling"
  ],
  "explanation": "The change is classified as fix because it corrects existing behavior in the login form.",
  "semver_suggestion": "patch",
  "full_command": "git commit -m \"fix(auth): resolve login form validation error\"",
  "warnings": []
}
""".strip()


STYLE_GUIDE = """
Commit styles:
- conventional: use type(optional scope): description.
- simple_english: concise English sentence, no mandatory type prefix unless useful.
- simple_spanish: concise technical sentence in Spanish.
- formal_business: professional, audit-friendly, concise wording.
- gitmoji: start with a relevant gitmoji and follow with a clear commit message.
- release_notes: write as a release-note entry describing the visible change.
""".strip()


TYPE_GUIDE = """
Change type rules:
- feat: new user-facing capability or functionality.
- fix: bug correction or broken behavior resolution.
- docs: documentation-only change.
- style: formatting, visual or code style changes that do not alter behavior.
- refactor: internal restructuring without changing behavior.
- test: adding or updating tests.
- chore: maintenance tasks that do not affect runtime behavior.
- perf: performance improvement.
- build: build system, packaging or dependency changes.
- ci: CI/CD configuration or automation changes.
- revert: reverting a previous change.
""".strip()


def build_commit_prompt(request: CommitGenerationRequest) -> str:
    scope_instruction = (
        f"Use this exact scope if the selected style supports scopes: {request.scope}."
        if request.scope
        else "Infer a scope only if it is clearly supported by the user's description. If not, omit the scope."
    )

    return f'''
You are an expert in Git, Conventional Commits, Semantic Versioning and technical writing for software teams.

Generate commit messages from the user's change description.

Return only valid JSON. Do not include markdown, comments, code fences, explanations outside JSON, or trailing text.
The JSON must match exactly this schema:
{JSON_SCHEMA_EXAMPLE}

User configuration:
- Commit style: {request.commit_style}
- Output language: {request.output_language}
- Selected change type: {request.change_type}
- Scope rule: {scope_instruction}
- Formality level: {request.formality_level}
- Number of alternatives requested: {request.alternatives_count}

User change description:
"""
{request.change_description}
"""

{STYLE_GUIDE}

{TYPE_GUIDE}

Generation rules:
1. Do not invent changes, features, files or scopes that the user did not mention or strongly imply.
2. If selected change type is "automatic", infer the most likely type conservatively.
3. If the output language is English, use clear technical English and lowercase the description in Conventional Commits.
4. If the output language is Spanish, use natural technical Spanish.
5. Commit messages must be short, specific and professional.
6. Do not end commit messages with a period.
7. Avoid generic messages such as "update changes", "fix stuff", "changes" or "improvements".
8. Alternatives must be meaningfully different, not small wording variations.
9. The alternatives array must contain exactly {request.alternatives_count} items separate from recommended_commit.
10. Suggest SemVer conservatively:
    - patch for fixes, refactors, docs, style, tests, chores, CI or build changes without public behavior changes.
    - minor for new backwards-compatible functionality.
    - major only for explicit breaking changes.
    - none for changes that should not affect released software.
11. Add warnings when the description is ambiguous, too broad, lacks context, or does not allow safe scope inference.
12. full_command must use the recommended_commit exactly inside: git commit -m "...".
13. Escape quotation marks inside JSON strings correctly.
14. The response must be parseable JSON.
'''.strip()
