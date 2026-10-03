with open("tests/test_providers.py", "r") as f:
    content = f.read()
content = content.replace('resp.usage = MagicMock(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)', 'resp.usage = MagicMock(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)\n    resp.model = "gpt-4o-mini"')
with open("tests/test_providers.py", "w") as f:
    f.write(content)
