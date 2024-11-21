import json
from collections import defaultdict

def get_primevul_pairs(pth, limit = -1):
    with open(pth, "r") as f:
        samples = f.readlines()
    samples = [json.loads(sample) for sample in samples]

    if limit != -1 and limit % 2 == 1:
        limit += 1

    # Step 1: Group relevant idx values by commit_url and file_name
    alpha_groups = defaultdict(list)
    for sample in samples:
        sample_idx = sample.get("idx")
        key = (sample.get("commit_url", None), None)
        alpha_groups[key].append(sample_idx)

        limit -= 1
        if limit == 0:
            break 

    # Step 2: Manually fix groups that are too large
    unpaired = {}
    fixed = {}
    rem_keys = []
    for key, sublist in alpha_groups.items():
        if len(sublist) > 2:
            rem_keys.append(key)
            print("\nToo many values in this group!")
            print(sublist)
            fixed_ids = []
            for i in range(0, len(sublist)//2):
                while True:
                    pair = input("Enter a pair of IDs separated by a comma, or -1 if no pairs exist: ")
                    split_pair = list(map(lambda x: int(x.strip()), pair.split(',')))
                    if len(split_pair) > 2:
                        print("Entry contains too many values. Please enter the IDs in pairs.")
                    elif split_pair[0] not in sublist or split_pair[1] not in sublist:
                        print("Invalid IDs entered, please try again.")
                    else:
                        break
                fixed_key = (key[0], key[1] or i)
                fixed[fixed_key] = split_pair
                fixed_ids.extend(split_pair)
            if len(sublist)%2 != 0:
                for val in sublist:
                    if val not in fixed_ids:
                        unpaired[val] = key
        elif len(sublist) < 2:
            rem_keys.append(key)
            for val in sublist:
                unpaired[val] = key
    
    # Step 2: Manually fix ungrouped entries
    isNone = False
    while len(unpaired) > 0:
        print("\nUNPAIRED:")
        valid_ids = []
        for id, key in unpaired.items():
            print(key, id) 
            valid_ids.append(id)

        while True:
            pair = input("Enter a pair of IDs separated by a comma, or -1 if no pairs exist: ")
            split_pair = list(map(lambda x: int(x.strip()), pair.split(',')))
            if split_pair[0] == -1:
                isNone = True
                break
            if len(split_pair) > 2:
                print("Entry contains too many values. Please enter the IDs in pairs.")
            elif split_pair[0] not in valid_ids or split_pair[1] not in valid_ids:
                print("Invalid IDs entered, please try again.")
            else:
                break
        if isNone:
            break
        else:
            fixed_key = (unpaired[split_pair[0]],unpaired[split_pair[1]])
            fixed[fixed_key] = split_pair
            del unpaired[split_pair[0]]
            del unpaired[split_pair[1]]

    # Remove the bad entries
    for key in rem_keys:
        del alpha_groups[key]

    # Add the new corrected groupings
    alpha_groups.update(fixed)

    return alpha_groups.values()