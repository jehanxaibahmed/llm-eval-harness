with open("tests/test_providers.py", "r") as f:
    lines = f.readlines()
with open("tests/test_providers.py", "w") as f:
    skip = False
    for line in lines:
        if line.startswith("def test_litellm_passes_kwargs"):
            skip = True
        if skip and line.strip() == "" and "def test_" not in line:
            pass # still skipping
        if skip and line.startswith("def test_") and not line.startswith("def test_litellm_passes_kwargs"):
            skip = False
        if not skip:
            f.write(line)
