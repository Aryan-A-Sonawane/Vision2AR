import json

# Load new knowledge base
kb = json.load(open('knowledge_base_v2.json', 'r', encoding='utf-8'))

print(f"Total procedures: {len(kb)}\n")

# Show overheating example
overheat = [p for p in kb if p['issue_type'] == 'overheating'][0]
print("Sample Overheating Procedure:")
print(f"  Symptoms: {overheat['symptoms']}")
print(f"  Steps: {len(overheat['solution_steps'])}")
print(f"  First step: {overheat['solution_steps'][0][:150]}...")
print(f"  Source: {overheat['source_file']}")
print()

# Show no_boot example
no_boot = [p for p in kb if p['issue_type'] == 'no_boot'][0]
print("Sample No Boot Procedure:")
print(f"  Symptoms: {no_boot['symptoms']}")
print(f"  Steps: {len(no_boot['solution_steps'])}")
print(f"  First step: {no_boot['solution_steps'][0][:150]}...")
print(f"  Source: {no_boot['source_file']}")
