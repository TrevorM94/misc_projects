from itertools import permutations

def can_fill_slots(groups):
    skills = set()
    for group in groups:
        for skill in group:
            skills.add(skill)
    if len(skills) != 6:
        return False

    def backtrack(index, slots, skill_counts):
        if index == 5:
            for slot in slots:
                print("Slot:", slot)
            return True

        for group in permutations(groups):
            if (index == 1 or group[0][0] not in [slot[0] for slot in slots]) and skill_counts[group[0][0]] < 2:
                new_slots = slots[:]
                new_slots.append(group[0])

                new_skill_counts = skill_counts.copy()
                for skill in group[0]:
                    new_skill_counts[skill] += 1

                if backtrack(index + 1, new_slots, new_skill_counts):
                    return True
        return False

    return backtrack(1, [], {skill: 0 for skill in skills})


groups = [
    "ABE", "FBA", "CAE", "BCE", "ACE", "BAC",
    "FCD", "DFA", "EFD", "CAB", "CBD", "ACD", "DCF", "CEF"
]

if can_fill_slots(groups):
    print("It is possible to fill the four slots.")
else:
    print("It is not possible to fill the four slots.")