import random
import json

true_conditions = ['Positive', 'Negative']
blind_labels = ['A', 'B']

random.shuffle(blind_labels)

assignment = {
    blind_labels[0]: true_conditions[0],
    blind_labels[1]: true_conditions[1],
}


json_text = json.dumps(assignment)

with open('blinding.txt', 'w') as outfile:
    json.dump(json_text, outfile)

with open('blinding.txt', 'r') as infile:
    json_text_read = json.load(infile)

assignment = json.loads(json_text_read)

