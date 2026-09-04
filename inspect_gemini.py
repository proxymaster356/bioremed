import os
from pathlib import Path

gemini_dir = Path('temp_claude_skills/.gemini')
if gemini_dir.exists():
    items = list(gemini_dir.iterdir())
    print('Items in .gemini:', [i.name for i in items])
    skills_dir = gemini_dir / 'skills'
    if skills_dir.exists():
        skills = list(skills_dir.iterdir())
        print('Total skills in .gemini/skills:', len(skills))
        print('Sample skills:', [s.name for s in skills[:15]])
