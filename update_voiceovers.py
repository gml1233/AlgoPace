import re

def process_file():
    with open('codetest/B-树的查找.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Normalize all single-line voiceovers to multiline
    # Pattern: with self.voiceover(text="something") as tracker:
    def repl_single(match):
        indent = match.group(1)
        text_content = match.group(2)
        
        # Prepare subcaption by ensuring it uses B-树
        subcaption = text_content.replace("B树", "B-树")
        # Prepare text by ensuring it uses B树
        text = text_content.replace("B-树", "B树")
        
        return f'{indent}with self.voiceover(\n{indent}    text="{text}",\n{indent}    subcaption="{subcaption}"\n{indent}) as tracker:'

    content = re.sub(r'^(\s*)with self\.voiceover\(text="([^"]+)"\) as tracker:', repl_single, content, flags=re.MULTILINE)

    # Step 2: Fix existing multiline voiceovers
    # Pattern: 
    # with self.voiceover(
    #     text="...",
    #     subcaption="..."
    # ) as tracker:
    
    def repl_multi(match):
        indent = match.group(1)
        text_content = match.group(2)
        subcaption_content = match.group(3)
        
        text = text_content.replace("B-树", "B树")
        subcaption = subcaption_content.replace("B树", "B-树")
        
        return f'{indent}with self.voiceover(\n{indent}    text="{text}",\n{indent}    subcaption="{subcaption}"\n{indent}) as tracker:'

    # This regex matches the multiline format
    pattern_multi = r'^(\s*)with self\.voiceover\(\s*text="([^"]+)",\s*subcaption="([^"]+)"\s*\) as tracker:'
    content = re.sub(pattern_multi, repl_multi, content, flags=re.MULTILINE)

    with open('codetest/B-树的查找.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    process_file()
