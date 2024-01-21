#!/usr/bin/env python

import json
import sppl.compilers.spe_to_dict as spe_to_dict

from sppl.transforms import Identity

with open("data/sppl/merged.json", "r") as f:
    spe_dict = json.load(f)

models  = spe_to_dict.spe_from_dict(spe_dict)

e = {Identity("race_ethnicity"):"Asian", Identity("religion_importance"):"Very Important"}
mc = models.constrain(e)
p_all = mc.prob(Identity("ideology") << {"Conservative", "Very Conservative"})
print(p_all)
print("children")
for i,m in enumerate(models.children):
    print(i)
    mc = m.constrain(e)
    p = mc.prob(Identity("ideology") << {"Conservative", "Very Conservative"})
    print(p)
    print(p - p_all)

mid = 9

m_out = models.children[mid]

with open("data/sppl/small-spe.json", "w") as f:
    json.dump(spe_to_dict.spe_to_dict(m_out), f)

